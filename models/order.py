from datetime import datetime
from decimal import Decimal
from database import db

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Order status
    status = db.Column(db.String(20), default='pending')  # pending, processing, shipped, delivered, cancelled, refunded
    
    # Customer information
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    
    # Billing address
    billing_first_name = db.Column(db.String(50), nullable=False)
    billing_last_name = db.Column(db.String(50), nullable=False)
    billing_company = db.Column(db.String(100), nullable=True)
    billing_address_1 = db.Column(db.String(200), nullable=False)
    billing_address_2 = db.Column(db.String(200), nullable=True)
    billing_city = db.Column(db.String(50), nullable=False)
    billing_state = db.Column(db.String(50), nullable=False)
    billing_postcode = db.Column(db.String(20), nullable=False)
    billing_country = db.Column(db.String(50), nullable=False)
    
    # Shipping address (can be same as billing)
    shipping_first_name = db.Column(db.String(50), nullable=True)
    shipping_last_name = db.Column(db.String(50), nullable=True)
    shipping_company = db.Column(db.String(100), nullable=True)
    shipping_address_1 = db.Column(db.String(200), nullable=True)
    shipping_address_2 = db.Column(db.String(200), nullable=True)
    shipping_city = db.Column(db.String(50), nullable=True)
    shipping_state = db.Column(db.String(50), nullable=True)
    shipping_postcode = db.Column(db.String(20), nullable=True)
    shipping_country = db.Column(db.String(50), nullable=True)
    
    # Order totals
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_fee = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Payment information
    payment_method = db.Column(db.String(50), nullable=True)  # credit_card, paypal, bank_transfer, etc.
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded
    transaction_id = db.Column(db.String(100), nullable=True)
    ecpay_trade_no = db.Column(db.String(50))  # ECPay transaction number
    
    # Shipping information
    shipping_method = db.Column(db.String(50), nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Notes
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    @property
    def customer_name(self):
        """Get customer full name"""
        return f"{self.billing_first_name} {self.billing_last_name}"
    
    @property
    def shipping_name(self):
        """Get shipping full name"""
        if self.shipping_first_name and self.shipping_last_name:
            return f"{self.shipping_first_name} {self.shipping_last_name}"
        return self.customer_name
    
    def get_status_display(self):
        """Get human-readable status"""
        status_map = {
            'pending': 'Pending',
            'processing': 'Processing',
            'shipped': 'Shipped',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled',
            'refunded': 'Refunded'
        }
        return status_map.get(self.status, self.status)
    
    def get_payment_status_display(self):
        """Get human-readable payment status"""
        status_map = {
            'pending': 'Pending',
            'paid': 'Paid',
            'failed': 'Failed',
            'refunded': 'Refunded'
        }
        return status_map.get(self.payment_status, self.payment_status)
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        import random
        import string
        
        while True:
            # Generate order number like ORD-20231201-ABC123
            date_str = datetime.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            order_number = f"ORD-{date_str}-{random_str}"
            
            # Check if order number already exists
            if not Order.query.filter_by(order_number=order_number).first():
                return order_number

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Product snapshot (in case product is deleted or changed)
    product_name = db.Column(db.String(200), nullable=False)
    product_sku = db.Column(db.String(100), nullable=False)
    product_image = db.Column(db.String(255), nullable=True)
    
    # Pricing snapshot
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OrderItem {self.product_name} x {self.quantity}>'
    
    @property
    def line_total(self):
        """Calculate line total"""
        return self.unit_price * self.quantity
