from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user, login_user, logout_user
from models import Product, Category, Cart, CartItem, Ads, Coupon, ShippingFee, User
from models.order import Order, OrderItem
from models.product import ProductImage
from utils.helpers import paginate_query, generate_slug, generate_order_number
from utils.image_utils import process_product_image, process_ad_image, delete_image
from app import db
import json
import os
from datetime import datetime, timedelta
from sqlalchemy import func
from tasks.order_status import sync_pending_orders

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_admin:
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    logout_user()
    return redirect(url_for('admin.login'))

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_categories = Category.query.count()
    total_users = User.query.count()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Low stock products
    low_stock_products = Product.query.filter(
        Product.stock_quantity <= 5,
        Product.manage_stock == True
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_categories=total_categories,
                         total_users=total_users,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products)

# Product Management
@admin_bp.route('/products')
@admin_required
def products():
    """Products list"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', '')
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.contains(search))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)
    
    products = paginate_query(query.order_by(Product.created_at.desc()), page, 20)
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('admin/products/list.html',
                         products=products,
                         categories=categories)

@admin_bp.route('/products/create', methods=['GET', 'POST'])
@admin_required
def create_product():
    """Create new product"""
    if request.method == 'POST':
        try:
            # Create product
            product = Product(
                name=request.form['name'],
                slug=generate_slug(request.form['name']),
                description=request.form.get('description', ''),
                short_description=request.form.get('short_description', ''),
                sku=request.form['sku'],
                regular_price=float(request.form['regular_price']),
                sale_price=float(request.form['sale_price']) if request.form.get('sale_price') else None,
                stock_quantity=int(request.form.get('stock_quantity', 0)),
                manage_stock=bool(request.form.get('manage_stock')),
                category_id=int(request.form['category_id']),
                status=request.form.get('status', 'draft'),
                featured=bool(request.form.get('featured')),
                is_active=bool(request.form.get('is_active'))
            )
            
            db.session.add(product)
            db.session.flush()  # Get the ID
            
            # Handle images
            if 'images' in request.files:
                files = request.files.getlist('images')
                for i, file in enumerate(files):
                    if file and file.filename:
                        image_path, error = process_product_image(file, product.id, i == 0, i)
                        if image_path:
                            product_image = ProductImage(
                                product_id=product.id,
                                image_path=image_path,
                                is_primary=(i == 0),
                                sort_order=i
                            )
                            db.session.add(product_image)
            
            db.session.commit()
            flash('Product created successfully', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating product: {str(e)}', 'error')
    
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('admin/products/create.html', categories=categories)

@admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    """Edit product"""
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            product.name = request.form['name']
            product.slug = generate_slug(request.form['name'])
            product.description = request.form.get('description', '')
            product.short_description = request.form.get('short_description', '')
            product.sku = request.form['sku']
            product.regular_price = float(request.form['regular_price'])
            product.sale_price = float(request.form['sale_price']) if request.form.get('sale_price') else None
            product.stock_quantity = int(request.form.get('stock_quantity', 0))
            product.manage_stock = bool(request.form.get('manage_stock'))
            product.category_id = int(request.form['category_id'])
            product.status = request.form.get('status', 'draft')
            product.featured = bool(request.form.get('featured'))
            product.is_active = bool(request.form.get('is_active'))
            
            # Handle new images
            if 'images' in request.files:
                files = request.files.getlist('images')
                for i, file in enumerate(files):
                    if file and file.filename:
                        image_path, error = process_product_image(file, product.id, False, len(product.images) + i)
                        if image_path:
                            product_image = ProductImage(
                                product_id=product.id,
                                image_path=image_path,
                                is_primary=False,
                                sort_order=len(product.images) + i
                            )
                            db.session.add(product_image)
            
            db.session.commit()
            flash('Product updated successfully', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'error')
    
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('admin/products/edit.html', product=product, categories=categories)

@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@admin_required
def delete_product(id):
    """Delete product"""
    product = Product.query.get_or_404(id)
    
    try:
        # Delete images
        for image in product.images:
            delete_image(f"static/{image.image_path}")
        
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
    
    return redirect(url_for('admin.products'))

# Category Management
@admin_bp.route('/categories')
@admin_required
def categories():
    """Categories list"""
    categories = Category.get_three_level_categories()
    return render_template('admin/categories/list.html', categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@admin_required
def create_category():
    """Create new category"""
    if request.method == 'POST':
        try:
            category = Category(
                name=request.form['name'],
                slug=generate_slug(request.form['name']),
                description=request.form.get('description', ''),
                parent_id=int(request.form['parent_id']) if request.form.get('parent_id') else None,
                is_parent=bool(request.form.get('is_parent')),
                sort_order=int(request.form.get('sort_order', 0)),
                is_active=bool(request.form.get('is_active'))
            )
            
            db.session.add(category)
            db.session.commit()
            flash('Category created successfully', 'success')
            return redirect(url_for('admin.categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating category: {str(e)}', 'error')
    
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('admin/categories/create.html', categories=categories)

# Order Management
@admin_bp.route('/orders')
@admin_required
def orders():
    """Orders list"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    
    orders = paginate_query(query.order_by(Order.created_at.desc()), page, 20)
    return render_template('admin/orders/list.html', orders=orders)

@admin_bp.route('/tools/pending-orders', methods=['GET', 'POST'])
@admin_required
def pending_orders_tool():
    """Admin tool to inspect and sync pending ECPay orders."""
    sync_info = None
    limit_value = 50

    if request.method == 'POST':
        limit = request.form.get('limit', type=int)
        limit_value = limit or 50
        try:
            sync_info = sync_pending_orders(limit=limit_value)
            updated = sync_info.get('updated', 0)
            message_type = 'success' if updated else 'info'
            flash(f"Synced {updated} pending orders.", message_type)
        except Exception as exc:
            current_app.logger.exception('Error syncing pending orders: %s', exc)
            flash(f"Error syncing pending orders: {exc}", 'error')

    pending_orders = (Order.query
                      .filter(Order.payment_status == 'pending')
                      .order_by(Order.created_at.asc())
                      .all())
    now = datetime.utcnow()

    return render_template('admin/tools/pending_orders.html',
                           pending_orders=pending_orders,
                           sync_info=sync_info,
                           now=now,
                           default_limit=limit_value)


@admin_bp.route('/orders/<int:id>')
@admin_required
def order_detail(id):
    """Order detail"""
    order = Order.query.get_or_404(id)
    return render_template('admin/orders/detail.html', order=order)

@admin_bp.route('/orders/<int:id>/update-status', methods=['POST'])
@admin_required
def update_order_status(id):
    """Update order status"""
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded', 'failed']:
        order.status = new_status
        db.session.commit()
        flash('Order status updated successfully', 'success')
    else:
        flash('Invalid status', 'error')
    
    return redirect(url_for('admin.order_detail', id=id))

# Advertisement Management
@admin_bp.route('/ads')
@admin_required
def ads():
    """Ads list"""
    ads = Ads.query.order_by(Ads.created_at.desc()).all()
    return render_template('admin/ads/list.html', ads=ads)


@admin_bp.route('/ads/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_ad(id):
    """Edit advertisement"""
    ad = Ads.query.get_or_404(id)

    if request.method == 'POST':
        ad.title = request.form['title']
        ad.description = request.form.get('description', '')
        ad.link_url = request.form.get('link_url', '')
        ad.position = request.form['position']
        ad.sort_order = int(request.form.get('sort_order', 0))
        ad.is_active = bool(request.form.get('is_active'))

        try:
            ad.status = 'active' if ad.is_active else 'inactive'
        except Exception:
            pass

        try:
            desktop_file = request.files.get('desktop_image')
            mobile_file = request.files.get('mobile_image')

            if request.form.get('remove_desktop_image'):
                if ad.desktop_image:
                    delete_image(os.path.join(current_app.root_path, 'static', ad.desktop_image.replace('/', os.sep)))
                    ad.desktop_image = None
            elif desktop_file and desktop_file.filename:
                if ad.desktop_image:
                    delete_image(os.path.join(current_app.root_path, 'static', ad.desktop_image.replace('/', os.sep)))
                desktop_path, error = process_ad_image(desktop_file, ad.id, 'desktop')
                if error or not desktop_path:
                    raise ValueError(error or 'Failed to process desktop image')
                ad.desktop_image = desktop_path

            if request.form.get('remove_mobile_image'):
                if ad.mobile_image:
                    delete_image(os.path.join(current_app.root_path, 'static', ad.mobile_image.replace('/', os.sep)))
                    ad.mobile_image = None
            elif mobile_file and mobile_file.filename:
                if ad.mobile_image:
                    delete_image(os.path.join(current_app.root_path, 'static', ad.mobile_image.replace('/', os.sep)))
                mobile_path, error = process_ad_image(mobile_file, ad.id, 'mobile')
                if error or not mobile_path:
                    raise ValueError(error or 'Failed to process mobile image')
                ad.mobile_image = mobile_path

            db.session.commit()
            flash('Advertisement updated successfully', 'success')
            return redirect(url_for('admin.ads'))
        except ValueError as err:
            db.session.rollback()
            flash(str(err), 'error')
        except Exception as exc:
            db.session.rollback()
            flash(f'Error updating advertisement: {exc}', 'error')

    return render_template('admin/ads/edit.html', ad=ad)


@admin_bp.route('/ads/<int:id>/delete', methods=['POST'])
@admin_required
def delete_ad(id):
    """Delete advertisement"""
    ad = Ads.query.get_or_404(id)

    try:
        if ad.desktop_image:
            delete_image(os.path.join(current_app.root_path, 'static', ad.desktop_image.replace('/', os.sep)))
        if ad.mobile_image:
            delete_image(os.path.join(current_app.root_path, 'static', ad.mobile_image.replace('/', os.sep)))

        db.session.delete(ad)
        db.session.commit()
        flash('Advertisement deleted successfully', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Error deleting advertisement: {exc}', 'error')

    return redirect(url_for('admin.ads'))

@admin_bp.route('/ads/create', methods=['GET', 'POST'])
@admin_required
def create_ad():
    """Create new ad"""
    if request.method == 'POST':
        try:
            ad = Ads(
                title=request.form['title'],
                description=request.form.get('description', ''),
                link_url=request.form.get('link_url', ''),
                position=request.form['position'],
                sort_order=int(request.form.get('sort_order', 0)),
                is_active=bool(request.form.get('is_active'))
            )

            # Keep legacy status column in sync if present
            try:
                ad.status = 'active' if ad.is_active else 'inactive'
            except Exception:
                pass
            
            db.session.add(ad)
            db.session.flush()  # Get the ID
            
            # Handle images
            if 'desktop_image' in request.files:
                file = request.files['desktop_image']
                if file and file.filename:
                    image_path, error = process_ad_image(file, ad.id, 'desktop')
                    if image_path:
                        ad.desktop_image = image_path
            
            if 'mobile_image' in request.files:
                file = request.files['mobile_image']
                if file and file.filename:
                    image_path, error = process_ad_image(file, ad.id, 'mobile')
                    if image_path:
                        ad.mobile_image = image_path
            
            db.session.commit()
            flash('Advertisement created successfully', 'success')
            return redirect(url_for('admin.ads'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating advertisement: {str(e)}', 'error')
    
    return render_template('admin/ads/create.html')

# Coupon Management
@admin_bp.route('/coupons')
@admin_required
def coupons():
    """Coupons list"""
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons/list.html', coupons=coupons)

@admin_bp.route('/coupons/create', methods=['GET', 'POST'])
@admin_required
def create_coupon():
    """Create new coupon"""
    if request.method == 'POST':
        try:
            coupon = Coupon(
                code=request.form['code'],
                name=request.form['name'],
                description=request.form.get('description', ''),
                discount_type=request.form['discount_type'],
                discount_value=float(request.form['discount_value']),
                minimum_amount=float(request.form.get('minimum_amount', 0)),
                maximum_discount=float(request.form['maximum_discount']) if request.form.get('maximum_discount') else None,
                usage_limit=int(request.form['usage_limit']) if request.form.get('usage_limit') else None,
                usage_limit_per_user=int(request.form.get('usage_limit_per_user', 1)),
                is_active=bool(request.form.get('is_active'))
            )
            
            db.session.add(coupon)
            db.session.commit()
            flash('Coupon created successfully', 'success')
            return redirect(url_for('admin.coupons'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating coupon: {str(e)}', 'error')
    
    return render_template('admin/coupons/create.html')

# Shipping Fee Management
@admin_bp.route('/shipping')
@admin_required
def shipping_fees():
    """Shipping fees list"""
    shipping_fees = ShippingFee.query.order_by(ShippingFee.sort_order).all()
    return render_template('admin/shipping/list.html', shipping_fees=shipping_fees)

@admin_bp.route('/shipping/create', methods=['GET', 'POST'])
@admin_required
def create_shipping_fee():
    """Create new shipping fee"""
    if request.method == 'POST':
        try:
            shipping_fee = ShippingFee(
                name=request.form['name'],
                description=request.form.get('description', ''),
                method_type=request.form['method_type'],
                cost=float(request.form.get('cost', 0)),
                free_shipping_threshold=float(request.form['free_shipping_threshold']) if request.form.get('free_shipping_threshold') else None,
                is_active=bool(request.form.get('is_active')),
                sort_order=int(request.form.get('sort_order', 0))
            )
            
            db.session.add(shipping_fee)
            db.session.commit()
            flash('Shipping fee created successfully', 'success')
            return redirect(url_for('admin.shipping_fees'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating shipping fee: {str(e)}', 'error')
    
    return render_template('admin/shipping/create.html')

