#!/usr/bin/env python3
"""
Database setup script for MVC Shopping
This script creates the database and initializes it with sample data
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from models import User, Category, Product, ProductImage, Cart, CartItem, Ads, Coupon, ShippingFee
from models.order import Order, OrderItem
from werkzeug.security import generate_password_hash

def create_database():
    """Create the database and tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Create sample data
        create_sample_data()
        
        print("Database setup completed successfully!")

def create_sample_data():
    """Create sample data for testing"""
    print("Creating sample data...")
    
    # Create admin user
    admin_user = User(
        username='admin',
        email='admin@mvcshopping.com',
        password_hash=generate_password_hash('admin123'),
        first_name='Admin',
        last_name='User',
        is_admin=True,
        is_active=True
    )
    db.session.add(admin_user)
    
    # Create regular user
    regular_user = User(
        username='customer',
        email='customer@mvcshopping.com',
        password_hash=generate_password_hash('customer123'),
        first_name='John',
        last_name='Doe',
        phone='123-456-7890',
        address='123 Main St, City, State 12345',
        is_active=True
    )
    db.session.add(regular_user)
    
    db.session.commit()
    print("Users created")
    
    # Create categories
    categories_data = [
        {
            'name': 'Electronics',
            'slug': 'electronics',
            'description': 'Electronic devices and accessories',
            'is_parent': True,
            'sort_order': 1
        },
        {
            'name': 'Clothing',
            'slug': 'clothing',
            'description': 'Fashion and apparel',
            'is_parent': True,
            'sort_order': 2
        },
        {
            'name': 'Home & Garden',
            'slug': 'home-garden',
            'description': 'Home improvement and garden supplies',
            'is_parent': True,
            'sort_order': 3
        }
    ]
    
    categories = {}
    for cat_data in categories_data:
        category = Category(**cat_data)
        db.session.add(category)
        db.session.flush()  # Get the ID
        categories[cat_data['slug']] = category
    
    # Create subcategories
    subcategories_data = [
        {
            'name': 'Smartphones',
            'slug': 'smartphones',
            'description': 'Mobile phones and accessories',
            'parent_id': categories['electronics'].id,
            'is_parent': False,
            'sort_order': 1
        },
        {
            'name': 'Laptops',
            'slug': 'laptops',
            'description': 'Portable computers',
            'parent_id': categories['electronics'].id,
            'is_parent': False,
            'sort_order': 2
        },
        {
            'name': 'Men\'s Clothing',
            'slug': 'mens-clothing',
            'description': 'Clothing for men',
            'parent_id': categories['clothing'].id,
            'is_parent': False,
            'sort_order': 1
        },
        {
            'name': 'Women\'s Clothing',
            'slug': 'womens-clothing',
            'description': 'Clothing for women',
            'parent_id': categories['clothing'].id,
            'is_parent': False,
            'sort_order': 2
        }
    ]
    
    for subcat_data in subcategories_data:
        subcategory = Category(**subcat_data)
        db.session.add(subcategory)
        db.session.flush()
        categories[subcat_data['slug']] = subcategory
    
    db.session.commit()
    print("Categories created")
    
    # Create products
    products_data = [
        {
            'name': 'iPhone 15 Pro',
            'slug': 'iphone-15-pro',
            'description': 'The latest iPhone with advanced features and premium design.',
            'short_description': 'Latest iPhone with advanced features',
            'sku': 'IPH15PRO-128',
            'regular_price': Decimal('999.00'),
            'sale_price': Decimal('899.00'),
            'stock_quantity': 50,
            'manage_stock': True,
            'category_id': categories['smartphones'].id,
            'status': 'published',
            'featured': True,
            'is_active': True,
            'weight': Decimal('0.187'),
            'dimensions': '14.67×7.15×0.83',
            'color': 'Space Black',
            'material': 'Titanium'
        },
        {
            'name': 'MacBook Pro 16"',
            'slug': 'macbook-pro-16',
            'description': 'Powerful laptop for professionals with M3 chip and stunning display.',
            'short_description': 'Professional laptop with M3 chip',
            'sku': 'MBP16-M3-512',
            'regular_price': Decimal('2499.00'),
            'stock_quantity': 25,
            'manage_stock': True,
            'category_id': categories['laptops'].id,
            'status': 'published',
            'featured': True,
            'is_active': True,
            'weight': Decimal('2.16'),
            'dimensions': '35.57×24.81×1.68',
            'color': 'Space Gray',
            'material': 'Aluminum'
        },
        {
            'name': 'Wireless Headphones',
            'slug': 'wireless-headphones',
            'description': 'High-quality wireless headphones with noise cancellation.',
            'short_description': 'Wireless headphones with noise cancellation',
            'sku': 'WH-001',
            'regular_price': Decimal('199.00'),
            'sale_price': Decimal('149.00'),
            'stock_quantity': 100,
            'manage_stock': True,
            'category_id': categories['electronics'].id,
            'status': 'published',
            'featured': False,
            'is_active': True,
            'weight': Decimal('0.25'),
            'color': 'Black',
            'material': 'Plastic'
        },
        {
            'name': 'Cotton T-Shirt',
            'slug': 'cotton-t-shirt',
            'description': 'Comfortable cotton t-shirt in various colors and sizes.',
            'short_description': 'Comfortable cotton t-shirt',
            'sku': 'TSHIRT-001',
            'regular_price': Decimal('29.99'),
            'stock_quantity': 200,
            'manage_stock': True,
            'category_id': categories['mens-clothing'].id,
            'status': 'published',
            'featured': False,
            'is_active': True,
            'color': 'White',
            'size': 'M',
            'material': '100% Cotton'
        },
        {
            'name': 'Garden Tools Set',
            'slug': 'garden-tools-set',
            'description': 'Complete set of garden tools for home gardening.',
            'short_description': 'Complete garden tools set',
            'sku': 'GARDEN-001',
            'regular_price': Decimal('79.99'),
            'sale_price': Decimal('59.99'),
            'stock_quantity': 75,
            'manage_stock': True,
            'category_id': categories['home-garden'].id,
            'status': 'published',
            'featured': False,
            'is_active': True,
            'weight': Decimal('2.5'),
            'material': 'Steel'
        }
    ]
    
    products = {}
    for product_data in products_data:
        product = Product(**product_data)
        db.session.add(product)
        db.session.flush()  # Get the ID
        products[product_data['slug']] = product
    
    db.session.commit()
    print("Products created")
    
    # Create sample cart for regular user
    cart = Cart(user_id=regular_user.id)
    db.session.add(cart)
    db.session.flush()
    
    # Add items to cart
    cart_items_data = [
        {
            'cart_id': cart.id,
            'product_id': products['iphone-15-pro'].id,
            'quantity': 1
        },
        {
            'cart_id': cart.id,
            'product_id': products['wireless-headphones'].id,
            'quantity': 2
        }
    ]
    
    for item_data in cart_items_data:
        cart_item = CartItem(**item_data)
        db.session.add(cart_item)
    
    db.session.commit()
    print("Cart created")
    
    # Create sample order
    order = Order(
        order_number='ORD-20241201-ABC123',
        user_id=regular_user.id,
        status='delivered',
        customer_email=regular_user.email,
        customer_phone=regular_user.phone,
        billing_first_name=regular_user.first_name,
        billing_last_name=regular_user.last_name,
        billing_address_1='123 Main St',
        billing_city='City',
        billing_state='State',
        billing_postcode='12345',
        billing_country='US',
        shipping_first_name=regular_user.first_name,
        shipping_last_name=regular_user.last_name,
        shipping_address_1='123 Main St',
        shipping_city='City',
        shipping_state='State',
        shipping_postcode='12345',
        shipping_country='US',
        subtotal=Decimal('1197.00'),
        shipping_fee=Decimal('0.00'),
        tax_amount=Decimal('95.76'),
        discount_amount=Decimal('0.00'),
        total_amount=Decimal('1292.76'),
        payment_method='credit_card',
        payment_status='paid',
        transaction_id='TXN123456789',
        shipping_method='standard',
        tracking_number='TRK123456789',
        shipped_at=datetime.utcnow(),
        delivered_at=datetime.utcnow()
    )
    db.session.add(order)
    db.session.flush()
    
    # Create order items
    order_items_data = [
        {
            'order_id': order.id,
            'product_id': products['iphone-15-pro'].id,
            'product_name': products['iphone-15-pro'].name,
            'product_sku': products['iphone-15-pro'].sku,
            'unit_price': products['iphone-15-pro'].current_price,
            'quantity': 1,
            'total_price': products['iphone-15-pro'].current_price
        },
        {
            'order_id': order.id,
            'product_id': products['wireless-headphones'].id,
            'product_name': products['wireless-headphones'].name,
            'product_sku': products['wireless-headphones'].sku,
            'unit_price': products['wireless-headphones'].current_price,
            'quantity': 2,
            'total_price': products['wireless-headphones'].current_price * 2
        }
    ]
    
    for item_data in order_items_data:
        order_item = OrderItem(**item_data)
        db.session.add(order_item)
    
    db.session.commit()
    print("Order created")
    
    # Create sample advertisements
    ads_data = [
        {
            'title': 'Summer Sale',
            'description': 'Get up to 50% off on all summer items',
            'position': 'homepage_banner',
            'sort_order': 1,
            'is_active': True,
            'start_date': datetime.utcnow(),
            'end_date': datetime(2024, 12, 31, 23, 59, 59)
        },
        {
            'title': 'New Arrivals',
            'description': 'Check out our latest products',
            'position': 'sidebar',
            'sort_order': 1,
            'is_active': True
        }
    ]
    
    for ad_data in ads_data:
        ad = Ads(**ad_data)
        db.session.add(ad)
    
    db.session.commit()
    print("Advertisements created")
    
    # Create sample coupons
    coupons_data = [
        {
            'code': 'WELCOME10',
            'name': 'Welcome Discount',
            'description': '10% off for new customers',
            'discount_type': 'percentage',
            'discount_value': Decimal('10.00'),
            'minimum_amount': Decimal('50.00'),
            'usage_limit': 100,
            'usage_limit_per_user': 1,
            'is_active': True,
            'start_date': datetime.utcnow(),
            'end_date': datetime(2024, 12, 31, 23, 59, 59)
        },
        {
            'code': 'SAVE20',
            'name': 'Save $20',
            'description': '$20 off orders over $100',
            'discount_type': 'fixed_amount',
            'discount_value': Decimal('20.00'),
            'minimum_amount': Decimal('100.00'),
            'usage_limit': 50,
            'usage_limit_per_user': 1,
            'is_active': True,
            'start_date': datetime.utcnow(),
            'end_date': datetime(2024, 12, 31, 23, 59, 59)
        }
    ]
    
    for coupon_data in coupons_data:
        coupon = Coupon(**coupon_data)
        db.session.add(coupon)
    
    db.session.commit()
    print("Coupons created")
    
    # Create shipping fees
    shipping_fees_data = [
        {
            'name': 'Standard Shipping',
            'description': 'Standard delivery within 5-7 business days',
            'method_type': 'flat_rate',
            'cost': Decimal('9.99'),
            'is_active': True,
            'sort_order': 1,
            'estimated_days_min': 5,
            'estimated_days_max': 7
        },
        {
            'name': 'Express Shipping',
            'description': 'Fast delivery within 2-3 business days',
            'method_type': 'flat_rate',
            'cost': Decimal('19.99'),
            'is_active': True,
            'sort_order': 2,
            'estimated_days_min': 2,
            'estimated_days_max': 3
        },
        {
            'name': 'Free Shipping',
            'description': 'Free shipping on orders over $250',
            'method_type': 'free_shipping',
            'cost': Decimal('0.00'),
            'free_shipping_threshold': Decimal('250.00'),
            'is_active': True,
            'sort_order': 3,
            'estimated_days_min': 5,
            'estimated_days_max': 7
        }
    ]
    
    for shipping_data in shipping_fees_data:
        shipping_fee = ShippingFee(**shipping_data)
        db.session.add(shipping_fee)
    
    db.session.commit()
    print("Shipping fees created")
    
    print("Sample data creation completed!")

if __name__ == '__main__':
    create_database()
