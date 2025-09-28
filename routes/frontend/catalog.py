
from datetime import datetime, timedelta

from flask import redirect, render_template, request, url_for
from sqlalchemy import func

from app import db
from models import Ads, Category, Product
from models.order import Order, OrderItem
from utils.helpers import paginate_query

from . import frontend_bp
from .helpers import get_user_wishlist_product_ids


@frontend_bp.route('/')
def index():
    """Homepage."""
    featured_products = Product.get_featured_products(8)
    new_arrivals = Product.get_new_arrivals(8)
    best_sellers = Product.get_best_sellers(8)
    on_sale_products = Product.get_on_sale_products(8)

    banners = Ads.get_homepage_banners()
    categories = Category.get_three_level_categories()
    wishlist_product_ids = get_user_wishlist_product_ids()

    deal_candidates = on_sale_products[:3]
    deal_products = []
    sales_map = {}

    if deal_candidates:
        product_ids = [product.id for product in deal_candidates]
        sales_rows = (
            db.session.query(
                OrderItem.product_id,
                func.coalesce(func.sum(OrderItem.quantity), 0).label('units_sold'),
                func.max(Order.created_at).label('last_order_at'),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.product_id.in_(product_ids))
            .filter(Order.status.notin_(['cancelled', 'refunded', 'failed']))
            .group_by(OrderItem.product_id)
            .all()
        )
        sales_map = {
            row.product_id: {
                'sold': int(row.units_sold or 0),
                'last_sale': row.last_order_at,
            }
            for row in sales_rows
        }

    now = datetime.utcnow()

    for product in deal_candidates:
        info = sales_map.get(product.id, {'sold': 0, 'last_sale': None})
        available = product.stock_quantity if product.manage_stock else None
        total_capacity = info['sold'] + (available if available is not None else 0)
        if available is not None and total_capacity > 0:
            progress = min(100, round((info['sold'] / total_capacity) * 100))
        elif info['sold'] > 0:
            progress = 100
        else:
            progress = 0

        reference_time = info['last_sale'] or product.updated_at
        end_time = None
        if reference_time:
            candidate = reference_time + timedelta(hours=24)
            if candidate > now:
                end_time = candidate.isoformat()

        deal_products.append(
            {
                'product': product,
                'sold': info['sold'],
                'available': available,
                'progress': progress,
                'end_time': end_time,
            }
        )

    return render_template(
        'frontend/index.html',
        featured_products=featured_products,
        new_arrivals=new_arrivals,
        best_sellers=best_sellers,
        on_sale_products=on_sale_products,
        banners=banners,
        categories=categories,
        wishlist_product_ids=wishlist_product_ids,
        deal_products=deal_products,
    )


@frontend_bp.route('/shop')
def shop():
    """Shop page with products listing."""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    query = Product.query.filter_by(is_active=True, status='published')

    if category_id:
        query = query.filter_by(category_id=category_id)

    if search:
        query = query.filter(
            db.or_(
                Product.name.contains(search),
                Product.description.contains(search),
                Product.short_description.contains(search),
            )
        )

    if min_price is not None:
        query = query.filter(Product.current_price >= min_price)
    if max_price is not None:
        query = query.filter(Product.current_price <= max_price)

    if sort_by == 'price_low':
        query = query.order_by(Product.current_price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.current_price.desc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc())
    elif sort_by == 'popular':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products = paginate_query(query, page, 12)
    categories = Category.get_three_level_categories()
    wishlist_product_ids = get_user_wishlist_product_ids()

    return render_template(
        'frontend/shop.html',
        products=products,
        categories=categories,
        current_category=category_id,
        search=search,
        sort_by=sort_by,
        min_price=min_price,
        max_price=max_price,
        wishlist_product_ids=wishlist_product_ids,
    )


@frontend_bp.route('/product/<slug>')
def product_detail(slug):
    """Product detail page."""
    product = Product.query.filter_by(
        slug=slug,
        is_active=True,
        status='published',
    ).first_or_404()

    related_products = (
        Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.is_active == True,  # noqa: E712
            Product.status == 'published',
        )
        .limit(4)
        .all()
    )

    wishlist_product_ids = get_user_wishlist_product_ids()
    product_in_wishlist = product.id in wishlist_product_ids

    return render_template(
        'frontend/product_detail.html',
        product=product,
        related_products=related_products,
        product_in_wishlist=product_in_wishlist,
        wishlist_product_ids=wishlist_product_ids,
    )


@frontend_bp.route('/category/<slug>')
def category(slug):
    """Category page."""
    category_obj = Category.query.filter_by(slug=slug, is_active=True).first_or_404()

    category_ids = [category_obj.id]
    category_ids.extend([c.id for c in category_obj.get_descendants()])

    page = request.args.get('page', 1, type=int)
    query = (
        Product.query.filter(
            Product.category_id.in_(category_ids),
            Product.is_active == True,  # noqa: E712
            Product.status == 'published',
        )
        .order_by(Product.created_at.desc())
    )

    products = paginate_query(query, page, 12)
    wishlist_product_ids = get_user_wishlist_product_ids()

    return render_template(
        'frontend/category.html',
        category=category_obj,
        products=products,
        wishlist_product_ids=wishlist_product_ids,
    )


@frontend_bp.route('/search')
def search():
    """Search results page."""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('frontend.shop'))
    return redirect(url_for('frontend.shop', search=query))
