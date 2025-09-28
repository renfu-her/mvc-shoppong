from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from decimal import Decimal
from models import Product, Category, Cart, CartItem, Ads, Coupon, ShippingFee, User, WishList
from models.order import Order, OrderItem
from utils.helpers import paginate_query, generate_order_number
from utils.ecpay import ECPayService, ECPAY_TEST_CONFIG
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

@frontend_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('frontend.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
        elif password != confirm_password:
            flash('Passwords do not match', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
        else:
            # Create new user
            from werkzeug.security import generate_password_hash
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('frontend.login'))
    
    return render_template('frontend/register.html')

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
    
    wishlist_product_ids = get_user_wishlist_product_ids()

    return render_template('frontend/index.html',
                         featured_products=featured_products,
                         new_arrivals=new_arrivals,
                         best_sellers=best_sellers,
                         on_sale_products=on_sale_products,
                         banners=banners,
                         categories=categories,
                         wishlist_product_ids=wishlist_product_ids)

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
    
    wishlist_product_ids = get_user_wishlist_product_ids()

    return render_template('frontend/shop.html',
                         products=products,
                         categories=categories,
                         current_category=category_id,
                         search=search,
                         sort_by=sort_by,
                         min_price=min_price,
                         max_price=max_price,
                         wishlist_product_ids=wishlist_product_ids)

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
    
    wishlist_product_ids = get_user_wishlist_product_ids()
    product_in_wishlist = product.id in wishlist_product_ids

    return render_template('frontend/product_detail.html',
                         product=product,
                         related_products=related_products,
                         product_in_wishlist=product_in_wishlist,
                         wishlist_product_ids=wishlist_product_ids)

@frontend_bp.route('/wishlist')
@login_required
def wishlist():
    """Display user's wishlist"""
    items = WishList.query.filter_by(user_id=current_user.id).order_by(WishList.created_at.desc()).all()
    return render_template('frontend/wishlist.html', items=items)

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

@frontend_bp.route('/checkout/process', methods=['POST'])
@login_required
def process_checkout():
    """Process checkout and redirect to ECPay"""
    cart = get_or_create_cart()
    cart_items = list(cart.items) if cart else []
    if not cart or not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('frontend.cart'))

    # Get form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    shipping_method_id = request.form.get('shipping_method')
    notes = request.form.get('notes', '')

    # Validation
    if not all([first_name, last_name, email, phone, address, shipping_method_id]):
        flash('Please fill in all required fields', 'error')
        return redirect(url_for('frontend.checkout'))

    # Get shipping method
    try:
        shipping_method_id = int(shipping_method_id)
    except (TypeError, ValueError):
        flash('Invalid shipping method', 'error')
        return redirect(url_for('frontend.checkout'))

    shipping_method = ShippingFee.query.get(shipping_method_id)
    if not shipping_method:
        flash('Invalid shipping method', 'error')
        return redirect(url_for('frontend.checkout'))

    # Calculate shipping cost
    shipping_cost = shipping_method.calculate_shipping_cost(order_amount=float(cart.subtotal))
    if shipping_cost is None:
        flash('Invalid shipping method for this order', 'error')
        return redirect(url_for('frontend.checkout'))

    order_subtotal = Decimal(str(cart.subtotal))
    shipping_cost_decimal = Decimal(str(shipping_cost))
    order_total = order_subtotal + shipping_cost_decimal

    # Create order
    order = Order(
        user_id=current_user.id,
        order_number=generate_order_number(),
        status='pending',
        customer_email=email,
        customer_phone=phone,
        billing_first_name=first_name,
        billing_last_name=last_name,
        billing_address_1=address,
        billing_city='Taipei',
        billing_state='Taiwan',
        billing_postcode='100',
        billing_country='TW',
        shipping_first_name=first_name,
        shipping_last_name=last_name,
        shipping_address_1=address,
        shipping_city='Taipei',
        shipping_state='Taiwan',
        shipping_postcode='100',
        shipping_country='TW',
        shipping_method=shipping_method.name,
        payment_method='ecpay',
        subtotal=order_subtotal,
        shipping_fee=shipping_cost_decimal,
        total_amount=order_total,
        customer_notes=notes,
        payment_status='pending'
    )
    db.session.add(order)
    db.session.flush()  # Get order ID

    # Create order items
    for item in cart_items:
        product = item.product
        if not product:
            continue

        unit_price = Decimal(str(product.sale_price or product.regular_price))
        total_price = unit_price * item.quantity
        primary_image = product.get_primary_image()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            product_image=primary_image.image_path if primary_image else None,
            unit_price=unit_price,
            quantity=item.quantity,
            total_price=total_price
        )
        db.session.add(order_item)

    # Initialize ECPay service
    ecpay_service = ECPayService(**ECPAY_TEST_CONFIG)
    merchant_trade_no = ecpay_service.generate_merchant_trade_no(order.id)
    order.transaction_id = merchant_trade_no

    db.session.commit()

    # Prepare order data for ECPay
    item_names = [f"{item.product.name} x {item.quantity}" for item in cart_items if item.product]
    item_name_str = '#'.join(item_names)

    order_data = {
        'merchant_trade_no': merchant_trade_no,
        'merchant_trade_date': ecpay_service.format_trade_date(),
        'total_amount': int(order.total_amount),
        'trade_desc': f"Order #{order.order_number}",
        'item_name': item_name_str,
        'return_url': url_for('frontend.ecpay_return', _external=True),
        'order_result_url': url_for('frontend.order_result', order_id=order.id, _external=True),
        'client_back_url': url_for('frontend.index', _external=True),
        'custom_field1': str(order.id),
        'custom_field2': f"{first_name} {last_name}",
        'custom_field3': email,
        'custom_field4': phone
    }

    # Create ECPay order
    ecpay_params = ecpay_service.create_order(order_data)

    # Store ECPay parameters in session for form submission
    session['ecpay_params'] = ecpay_params
    session['order_id'] = order.id

    # Clear cart after creating order
    cart.clear()

    return render_template('frontend/ecpay_redirect.html', 
                         ecpay_params=ecpay_params,
                         ecpay_url=ecpay_service.api_url)

@frontend_bp.route('/ecpay/return', methods=['POST'])
def ecpay_return():
    """ECPay payment result notification (server-to-server)"""
    ecpay_service = ECPayService(**ECPAY_TEST_CONFIG)
    form_data = request.form.to_dict()

    if not ecpay_service.verify_check_mac_value(form_data.copy()):
        return '0|CheckMacValue verification failed'

    merchant_trade_no = form_data.get('MerchantTradeNo')
    rtn_code = form_data.get('RtnCode')
    trade_no = form_data.get('TradeNo')
    payment_type = form_data.get('PaymentType')
    custom_field1 = form_data.get('CustomField1')

    order = None
    if custom_field1 and custom_field1.isdigit():
        order = Order.query.get(int(custom_field1))
    if not order and merchant_trade_no:
        order = Order.query.filter_by(transaction_id=merchant_trade_no).first()

    if not order:
        return '0|OrderNotFound'

    if rtn_code == '1':
        order.payment_status = 'paid'
        order.status = 'processing'
        if trade_no:
            order.ecpay_trade_no = trade_no
        if merchant_trade_no:
            order.transaction_id = merchant_trade_no
    else:
        order.payment_status = 'failed'
        if order.status == 'processing':
            order.status = 'pending'

    if payment_type:
        order.payment_method = payment_type

    db.session.commit()
    return '1|OK'


@frontend_bp.route('/order/result/<int:order_id>', methods=['GET', 'POST'])
def order_result(order_id):
    """Order result page after payment or gateway callback"""
    order = Order.query.get_or_404(order_id)

    if request.method == 'POST':
        form_data = request.form.to_dict()
        ecpay_service = ECPayService(**ECPAY_TEST_CONFIG)
        if ecpay_service.verify_check_mac_value(form_data.copy()):
            merchant_trade_no = form_data.get('MerchantTradeNo')
            rtn_code = form_data.get('RtnCode')
            trade_no = form_data.get('TradeNo')
            payment_type = form_data.get('PaymentType')

            if merchant_trade_no:
                order.transaction_id = merchant_trade_no
            if payment_type:
                order.payment_method = payment_type

            if rtn_code == '1':
                order.payment_status = 'paid'
                order.status = 'processing'
                if trade_no:
                    order.ecpay_trade_no = trade_no
            else:
                order.payment_status = 'failed'
                if order.status == 'processing':
                    order.status = 'pending'

            db.session.commit()
        return redirect(url_for('frontend.order_result', order_id=order.id))

    if not current_user.is_authenticated:
        return redirect(url_for('frontend.login', next=request.path))

    if order.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('frontend.index'))

    return render_template('frontend/order_result.html', order=order)


@frontend_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with order history"""
    user = current_user

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        user.first_name = first_name or None
        user.last_name = last_name or None
        user.phone = phone or None
        user.address = address or None

        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('frontend.profile'))

    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()

    order_stats = {
        'total': len(orders),
        'pending': sum(1 for order in orders if order.status == 'pending'),
        'processing': sum(1 for order in orders if order.status == 'processing'),
        'completed': sum(1 for order in orders if order.status in {'shipped', 'delivered'}),
        'cancelled': sum(1 for order in orders if order.status in {'cancelled', 'refunded'})
    }

    return render_template('frontend/profile.html',
                           user=user,
                           orders=orders,
                           order_stats=order_stats)

@frontend_bp.route('/ecpay/test-info')
def ecpay_test_info():
    """ECPay test information page"""
    return render_template('frontend/ecpay_test_info.html')

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
    
    wishlist_product_ids = get_user_wishlist_product_ids()

    return render_template('frontend/category.html',
                         category=category,
                         products=products,
                         wishlist_product_ids=wishlist_product_ids)

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

@frontend_bp.route('/api/wishlist/toggle', methods=['POST'])
@login_required
def api_toggle_wishlist():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please log in to manage your wishlist.', 'requires_login': True}), 401

    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID required'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1

    wishlist_item = WishList.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed', 'count': get_wishlist_count()})

    wishlist_item = WishList(user_id=current_user.id, product_id=product_id, quantity=quantity)
    db.session.add(wishlist_item)
    db.session.commit()

    return jsonify({'success': True, 'action': 'added', 'count': get_wishlist_count()})


@frontend_bp.route('/api/wishlist/count')
def api_wishlist_count():
    return jsonify({'count': get_wishlist_count()})


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

def get_user_wishlist_product_ids():
    if current_user.is_authenticated:
        return {item.product_id for item in WishList.query.filter_by(user_id=current_user.id)}
    return set()


def get_wishlist_count():
    if current_user.is_authenticated:
        return WishList.query.filter_by(user_id=current_user.id).count()
    return 0
