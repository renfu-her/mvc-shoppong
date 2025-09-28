
from datetime import datetime, timedelta

from flask import render_template
from sqlalchemy import func

from app import db
from models import Category, Product, User
from models.order import Order, OrderItem

from . import admin_bp, admin_required


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

    analysis_days = 14
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=analysis_days - 1)

    order_rows = (
        db.session.query(
            func.date(Order.created_at).label('order_date'),
            func.count(Order.id).label('order_count'),
            func.coalesce(func.sum(Order.total_amount), 0).label('order_total'),
        )
        .filter(Order.created_at >= start_date)
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

    product_rows = (
        db.session.query(
            Product.name.label('product_name'),
            func.coalesce(func.sum(OrderItem.quantity), 0).label('units_sold'),
            func.coalesce(func.sum(OrderItem.total_price), 0).label('revenue'),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= start_date)
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

    analysis_range_label = f"{start_date.strftime('%b %d')} - {today.strftime('%b %d, %Y')}"

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
    )
