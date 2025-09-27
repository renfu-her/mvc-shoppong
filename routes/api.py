from flask import Blueprint, request, jsonify
from models import Product, Category, Cart, CartItem
from models.order import Order, OrderItem
from utils.helpers import success_response, error_response
from app import db
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/products')
def get_products():
    """Get products API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    featured = request.args.get('featured', type=bool)
    
    query = Product.query.filter_by(is_active=True, status='published')
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    if featured:
        query = query.filter_by(featured=True)
    
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    products_data = []
    for product in products.items:
        primary_image = product.get_primary_image()
        products_data.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'description': product.short_description,
            'price': float(product.current_price),
            'regular_price': float(product.regular_price),
            'sale_price': float(product.sale_price) if product.sale_price else None,
            'discount_percentage': product.discount_percentage,
            'is_on_sale': product.is_on_sale,
            'is_in_stock': product.is_in_stock,
            'stock_quantity': product.stock_quantity,
            'image': f"/static/{primary_image.image_path}" if primary_image else None,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
                'slug': product.category.slug
            } if product.category else None
        })
    
    return success_response('Products retrieved successfully', {
        'products': products_data,
        'pagination': {
            'page': products.page,
            'pages': products.pages,
            'per_page': products.per_page,
            'total': products.total,
            'has_next': products.has_next,
            'has_prev': products.has_prev
        }
    })

@api_bp.route('/products/<int:product_id>')
def get_product(product_id):
    """Get single product API"""
    product = Product.query.filter_by(id=product_id, is_active=True, status='published').first()
    
    if not product:
        return error_response('Product not found', 404)
    
    images = []
    for image in product.get_all_images():
        images.append({
            'id': image.id,
            'url': f"/static/{image.image_path}",
            'thumbnail': f"/static/uploads/products/{product.id}/thumb_{image.image_path.split('/')[-1]}",
            'is_primary': image.is_primary,
            'alt_text': image.alt_text
        })
    
    product_data = {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'description': product.description,
        'short_description': product.short_description,
        'sku': product.sku,
        'price': float(product.current_price),
        'regular_price': float(product.regular_price),
        'sale_price': float(product.sale_price) if product.sale_price else None,
        'discount_percentage': product.discount_percentage,
        'is_on_sale': product.is_on_sale,
        'is_in_stock': product.is_in_stock,
        'stock_quantity': product.stock_quantity,
        'weight': float(product.weight) if product.weight else None,
        'dimensions': product.dimensions,
        'color': product.color,
        'size': product.size,
        'material': product.material,
        'images': images,
        'category': {
            'id': product.category.id,
            'name': product.category.name,
            'slug': product.category.slug
        } if product.category else None
    }
    
    return success_response('Product retrieved successfully', product_data)

@api_bp.route('/categories')
def get_categories():
    """Get categories API"""
    categories = Category.get_three_level_categories()
    
    categories_data = []
    for category_data in categories:
        category = category_data['category']
        children_data = []
        
        for child_data in category_data['children']:
            child = child_data['category']
            grandchildren_data = []
            
            for grandchild in child_data['children']:
                grandchildren_data.append({
                    'id': grandchild.id,
                    'name': grandchild.name,
                    'slug': grandchild.slug,
                    'description': grandchild.description,
                    'image': f"/static/{grandchild.image}" if grandchild.image else None
                })
            
            children_data.append({
                'id': child.id,
                'name': child.name,
                'slug': child.slug,
                'description': child.description,
                'image': f"/static/{child.image}" if child.image else None,
                'children': grandchildren_data
            })
        
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'image': f"/static/{category.image}" if category.image else None,
            'children': children_data
        })
    
    return success_response('Categories retrieved successfully', categories_data)

@api_bp.route('/cart', methods=['GET'])
def get_cart():
    """Get cart API"""
    # This would need session management
    # For now, return empty cart
    return success_response('Cart retrieved successfully', {
        'items': [],
        'subtotal': 0,
        'total': 0,
        'item_count': 0
    })

@api_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add item to cart API"""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return error_response('Product ID required')
    
    product = Product.query.get(product_id)
    if not product:
        return error_response('Product not found', 404)
    
    if not product.is_in_stock:
        return error_response('Product out of stock')
    
    # This would need proper cart management
    # For now, just return success
    return success_response('Item added to cart successfully')

@api_bp.route('/orders', methods=['POST'])
def create_order():
    """Create order API"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['customer_email', 'billing_first_name', 'billing_last_name', 
                      'billing_address_1', 'billing_city', 'billing_state', 
                      'billing_postcode', 'billing_country', 'items']
    
    for field in required_fields:
        if field not in data:
            return error_response(f'{field} is required')
    
    try:
        # Create order
        order = Order(
            order_number=Order.generate_order_number(),
            customer_email=data['customer_email'],
            customer_phone=data.get('customer_phone'),
            billing_first_name=data['billing_first_name'],
            billing_last_name=data['billing_last_name'],
            billing_company=data.get('billing_company'),
            billing_address_1=data['billing_address_1'],
            billing_address_2=data.get('billing_address_2'),
            billing_city=data['billing_city'],
            billing_state=data['billing_state'],
            billing_postcode=data['billing_postcode'],
            billing_country=data['billing_country'],
            shipping_first_name=data.get('shipping_first_name', data['billing_first_name']),
            shipping_last_name=data.get('shipping_last_name', data['billing_last_name']),
            shipping_company=data.get('shipping_company'),
            shipping_address_1=data.get('shipping_address_1', data['billing_address_1']),
            shipping_address_2=data.get('shipping_address_2'),
            shipping_city=data.get('shipping_city', data['billing_city']),
            shipping_state=data.get('shipping_state', data['billing_state']),
            shipping_postcode=data.get('shipping_postcode', data['billing_postcode']),
            shipping_country=data.get('shipping_country', data['billing_country']),
            payment_method=data.get('payment_method'),
            customer_notes=data.get('customer_notes')
        )
        
        db.session.add(order)
        db.session.flush()  # Get the ID
        
        # Calculate totals
        subtotal = 0
        
        # Add order items
        for item_data in data['items']:
            product = Product.query.get(item_data['product_id'])
            if not product:
                return error_response(f'Product {item_data["product_id"]} not found')
            
            quantity = item_data['quantity']
            unit_price = product.current_price
            total_price = unit_price * quantity
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                product_image=product.get_primary_image().image_path if product.get_primary_image() else None,
                unit_price=unit_price,
                quantity=quantity,
                total_price=total_price
            )
            
            db.session.add(order_item)
            subtotal += total_price
        
        # Set order totals
        order.subtotal = subtotal
        order.shipping_fee = data.get('shipping_fee', 0)
        order.tax_amount = data.get('tax_amount', 0)
        order.discount_amount = data.get('discount_amount', 0)
        order.total_amount = subtotal + order.shipping_fee + order.tax_amount - order.discount_amount
        
        db.session.commit()
        
        return success_response('Order created successfully', {
            'order_id': order.id,
            'order_number': order.order_number,
            'total_amount': float(order.total_amount)
        })
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error creating order: {str(e)}')

@api_bp.route('/orders/<int:order_id>')
def get_order(order_id):
    """Get order details API"""
    order = Order.query.get(order_id)
    
    if not order:
        return error_response('Order not found', 404)
    
    items_data = []
    for item in order.items:
        items_data.append({
            'id': item.id,
            'product_name': item.product_name,
            'product_sku': item.product_sku,
            'product_image': f"/static/{item.product_image}" if item.product_image else None,
            'unit_price': float(item.unit_price),
            'quantity': item.quantity,
            'total_price': float(item.total_price)
        })
    
    order_data = {
        'id': order.id,
        'order_number': order.order_number,
        'status': order.status,
        'status_display': order.get_status_display(),
        'payment_status': order.payment_status,
        'payment_status_display': order.get_payment_status_display(),
        'customer_name': order.customer_name,
        'customer_email': order.customer_email,
        'customer_phone': order.customer_phone,
        'subtotal': float(order.subtotal),
        'shipping_fee': float(order.shipping_fee),
        'tax_amount': float(order.tax_amount),
        'discount_amount': float(order.discount_amount),
        'total_amount': float(order.total_amount),
        'payment_method': order.payment_method,
        'shipping_method': order.shipping_method,
        'tracking_number': order.tracking_number,
        'created_at': order.created_at.isoformat(),
        'items': items_data
    }
    
    return success_response('Order retrieved successfully', order_data)
