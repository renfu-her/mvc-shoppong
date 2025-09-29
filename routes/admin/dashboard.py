
from datetime import datetime, timedelta

from flask import render_template, request, jsonify
from sqlalchemy import func

from app import db
from models import Category, Product, User
from models.order import Order, OrderItem

from . import admin_bp, admin_required


def get_date_range_from_request():
    """Extract date range from request parameters."""
    # Get parameters
    days = request.args.get('days', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    today = datetime.utcnow().date()
    
    # If specific date range provided
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            # Ensure end_date is not in the future
            if end_date > today:
                end_date = today
            return start_date, end_date
        except ValueError:
            pass
    
    # If days parameter provided
    if days:
        analysis_days = min(days, 365)  # Limit to 1 year max
    else:
        analysis_days = 14  # Default
    
    start_date = today - timedelta(days=analysis_days - 1)
    return start_date, today


def get_chart_data(start_date, end_date):
    """Get chart data for the specified date range."""
    # Calculate analysis days for iteration
    analysis_days = (end_date - start_date).days + 1
    
    # Order trend data
    order_rows = (
        db.session.query(
            func.date(Order.created_at).label('order_date'),
            func.count(Order.id).label('order_count'),
            func.coalesce(func.sum(Order.total_amount), 0).label('order_total'),
        )
        .filter(Order.created_at >= start_date)
        .filter(Order.created_at <= datetime.combine(end_date, datetime.max.time()))
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )

    order_map = {
        row.order_date: {
            'orders': row.order_count or 0,
            'revenue': float(row.order_total or 0),
        }
        for row in order_rows
    }

    order_chart_data = []
    for offset in range(analysis_days):
        day = start_date + timedelta(days=offset)
        stats = order_map.get(day, {'orders': 0, 'revenue': 0.0})
        order_chart_data.append(
            {
                'date': day.strftime('%Y-%m-%d'),
                'orders': int(stats['orders']),
                'revenue': float(stats['revenue']),
            }
        )

    # Product performance data
    product_rows = (
        db.session.query(
            Product.name.label('product_name'),
            func.coalesce(func.sum(OrderItem.quantity), 0).label('units_sold'),
            func.coalesce(func.sum(OrderItem.total_price), 0).label('revenue'),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= start_date)
        .filter(Order.created_at <= datetime.combine(end_date, datetime.max.time()))
        .filter(Order.status.notin_(['cancelled', 'refunded', 'failed']))
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )

    product_chart_data = [
        {
            'name': row.product_name,
            'units': int(row.units_sold or 0),
            'revenue': float(row.revenue or 0),
        }
        for row in product_rows
    ]
    
    return order_chart_data, product_chart_data


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard."""
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_categories = Category.query.count()
    total_users = User.query.count()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    low_stock_products = (
        Product.query.filter(
            Product.stock_quantity <= 5,
            Product.manage_stock == True,  # noqa: E712
        )
        .limit(10)
        .all()
    )

    # Get date range
    start_date, end_date = get_date_range_from_request()
    
    # Get chart data
    order_chart_data, product_chart_data = get_chart_data(start_date, end_date)
    
    # Create analysis range label
    analysis_range_label = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

    return render_template(
        'admin/dashboard.html',
        total_products=total_products,
        total_orders=total_orders,
        total_categories=total_categories,
        total_users=total_users,
        recent_orders=recent_orders,
        low_stock_products=low_stock_products,
        order_chart_data=order_chart_data,
        product_chart_data=product_chart_data,
        analysis_range_label=analysis_range_label,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
    )


@admin_bp.route('/chart-data')
@admin_required
def chart_data():
    """AJAX endpoint for updating chart data."""
    try:
        # Get date range
        start_date, end_date = get_date_range_from_request()
        
        # Get chart data
        order_chart_data, product_chart_data = get_chart_data(start_date, end_date)
        
        # Create analysis range label
        analysis_range_label = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        
        return jsonify({
            'success': True,
            'order_chart_data': order_chart_data,
            'product_chart_data': product_chart_data,
            'analysis_range_label': analysis_range_label,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
