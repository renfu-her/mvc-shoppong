from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from models import Product, Category, Cart, CartItem, Ads, Coupon, ShippingFee, User
from models.order import Order, OrderItem
from utils.helpers import paginate_query, generate_order_number
from app import db
import json

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('frontend.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('frontend.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('frontend/login.html')

@frontend_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('frontend.index'))

@frontend_bp.route('/')
def index():
    """Homepage"""
    # Get featured products
    featured_products = Product.get_featured_products(8)
    new_arrivals = Product.get_new_arrivals(8)
    best_sellers = Product.get_best_sellers(8)
    on_sale_products = Product.get_on_sale_products(8)
    
    # Get homepage banners
    banners = Ads.get_homepage_banners()
    
    # Get categories
    categories = Category.get_three_level_categories()
    
    return render_template('frontend/index.html',
                         featured_products=featured_products,
                         new_arrivals=new_arrivals,
                         best_sellers=best_sellers,
                         on_sale_products=on_sale_products,
                         banners=banners,
                         categories=categories)

@frontend_bp.route('/shop')
def shop():
    """Shop page with products listing"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # Build query
    query = Product.query.filter_by(is_active=True, status='published')
    
    # Filter by category
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Search filter
    if search:
        query = query.filter(
            db.or_(
                Product.name.contains(search),
                Product.description.contains(search),
                Product.short_description.contains(search)
            )
        )
    
    # Price filter
    if min_price is not None:
        query = query.filter(Product.current_price >= min_price)
    if max_price is not None:
        query = query.filter(Product.current_price <= max_price)
    
    # Sorting
    if sort_by == 'price_low':
        query = query.order_by(Product.current_price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.current_price.desc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc())
    elif sort_by == 'popular':
        # This would need a more complex query with order items
        query = query.order_by(Product.created_at.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())
    
    # Paginate
    products = paginate_query(query, page, 12)
    
    # Get categories for filter
    categories = Category.get_three_level_categories()
    
    return render_template('frontend/shop.html',
                         products=products,
                         categories=categories,
                         current_category=category_id,
                         search=search,
                         sort_by=sort_by,
                         min_price=min_price,
                         max_price=max_price)

@frontend_bp.route('/product/<slug>')
def product_detail(slug):
    """Product detail page"""
    product = Product.query.filter_by(slug=slug, is_active=True, status='published').first_or_404()
    
    # Get related products
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True,
        Product.status == 'published'
    ).limit(4).all()
    
    return render_template('frontend/product_detail.html',
                         product=product,
                         related_products=related_products)

@frontend_bp.route('/cart')
def cart():
    """Shopping cart page"""
    cart = get_or_create_cart()
    return render_template('frontend/cart.html', cart=cart)

@frontend_bp.route('/checkout')
@login_required
def checkout():
    """Checkout page - requires login"""
    cart = get_or_create_cart()
    if not cart or not cart.items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('frontend.cart'))
    
    # Get shipping methods
    shipping_methods = ShippingFee.get_available_shipping_methods(
        order_amount=float(cart.subtotal)
    )
    
    return render_template('frontend/checkout.html',
                         cart=cart,
                         shipping_methods=shipping_methods)

@frontend_bp.route('/category/<slug>')
def category(slug):
    """Category page"""
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Get products in this category and subcategories
    category_ids = [category.id]
    category_ids.extend([c.id for c in category.get_descendants()])
    
    page = request.args.get('page', 1, type=int)
    query = Product.query.filter(
        Product.category_id.in_(category_ids),
        Product.is_active == True,
        Product.status == 'published'
    ).order_by(Product.created_at.desc())
    
    products = paginate_query(query, page, 12)
    
    return render_template('frontend/category.html',
                         category=category,
                         products=products)

@frontend_bp.route('/search')
def search():
    """Search results page"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('frontend.shop'))
    
    return redirect(url_for('frontend.shop', search=query))

# API Routes for AJAX
@frontend_bp.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    """Add item to cart via AJAX"""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID required'})
    
    product = Product.query.get_or_404(product_id)
    if not product.is_in_stock:
        return jsonify({'success': False, 'message': 'Product out of stock'})
    
    cart = get_or_create_cart()
    cart.add_item(product_id, quantity)
    
    return jsonify({
        'success': True,
        'message': 'Item added to cart',
        'cart_count': cart.total_items
    })

@frontend_bp.route('/api/cart/update', methods=['POST'])
def api_update_cart():
    """Update cart item quantity via AJAX"""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID required'})
    
    cart = get_or_create_cart()
    cart.update_item_quantity(product_id, quantity)
    
    return jsonify({
        'success': True,
        'message': 'Cart updated',
        'cart_count': cart.total_items,
        'subtotal': float(cart.subtotal)
    })

@frontend_bp.route('/api/cart/remove', methods=['POST'])
def api_remove_from_cart():
    """Remove item from cart via AJAX"""
    data = request.get_json()
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID required'})
    
    cart = get_or_create_cart()
    cart.remove_item(product_id)
    
    return jsonify({
        'success': True,
        'message': 'Item removed from cart',
        'cart_count': cart.total_items,
        'subtotal': float(cart.subtotal)
    })

@frontend_bp.route('/api/cart/count')
def api_cart_count():
    """Get cart item count via AJAX"""
    cart = get_or_create_cart()
    return jsonify({'count': cart.total_items})

@frontend_bp.route('/api/validate-coupon', methods=['POST'])
def api_validate_coupon():
    """Validate coupon code via AJAX"""
    data = request.get_json()
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({'success': False, 'message': 'Coupon code required'})
    
    cart = get_or_create_cart()
    product_ids = [item.product_id for item in cart.items]
    
    coupon, message = Coupon.validate_coupon_code(
        code=code,
        order_amount=float(cart.subtotal),
        product_ids=product_ids
    )
    
    if coupon:
        discount = coupon.calculate_discount(float(cart.subtotal))
        return jsonify({
            'success': True,
            'message': 'Coupon applied successfully',
            'discount': float(discount),
            'coupon_code': coupon.code
        })
    else:
        return jsonify({'success': False, 'message': message})

def get_or_create_cart():
    """Get or create cart for current user/session"""
    from flask_login import current_user
    
    if current_user.is_authenticated:
        cart = Cart.get_or_create_cart(user_id=current_user.id)
    else:
        session_id = session.get('session_id')
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        cart = Cart.get_or_create_cart(session_id=session_id)
    
    return cart
