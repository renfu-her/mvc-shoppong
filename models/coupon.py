from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db

class Coupon(db.Model):
    __tablename__ = 'coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Discount type and amount
    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed_amount
    discount_value = db.Column(db.Decimal(10, 2), nullable=False)
    minimum_amount = db.Column(db.Decimal(10, 2), default=0)  # Minimum order amount to use coupon
    maximum_discount = db.Column(db.Decimal(10, 2), nullable=True)  # Maximum discount amount for percentage coupons
    
    # Usage limits
    usage_limit = db.Column(db.Integer, nullable=True)  # Total usage limit
    usage_limit_per_user = db.Column(db.Integer, default=1)  # Usage limit per user
    used_count = db.Column(db.Integer, default=0)  # Current usage count
    
    # Date range
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Product/Category restrictions
    applicable_products = db.Column(db.Text, nullable=True)  # JSON array of product IDs
    applicable_categories = db.Column(db.Text, nullable=True)  # JSON array of category IDs
    excluded_products = db.Column(db.Text, nullable=True)  # JSON array of product IDs
    excluded_categories = db.Column(db.Text, nullable=True)  # JSON array of category IDs
    
    # User restrictions
    applicable_users = db.Column(db.Text, nullable=True)  # JSON array of user IDs
    new_customers_only = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Coupon {self.code}>'
    
    def is_valid(self, user_id=None, order_amount=0, product_ids=None):
        """Check if coupon is valid for given conditions"""
        now = datetime.utcnow()
        
        # Check if coupon is active
        if not self.is_active:
            return False, "Coupon is not active"
        
        # Check date range
        if self.start_date and now < self.start_date:
            return False, "Coupon is not yet valid"
        
        if self.end_date and now > self.end_date:
            return False, "Coupon has expired"
        
        # Check usage limit
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "Coupon usage limit exceeded"
        
        # Check minimum order amount
        if order_amount < self.minimum_amount:
            return False, f"Minimum order amount of ${self.minimum_amount} required"
        
        # Check user restrictions
        if user_id:
            if self.new_customers_only:
                from models.order import Order
                if Order.query.filter_by(user_id=user_id).first():
                    return False, "Coupon is only valid for new customers"
            
            if self.applicable_users:
                import json
                try:
                    applicable_users = json.loads(self.applicable_users)
                    if user_id not in applicable_users:
                        return False, "Coupon is not applicable to this user"
                except:
                    pass
        
        # Check product restrictions
        if product_ids:
            import json
            
            # Check excluded products
            if self.excluded_products:
                try:
                    excluded_products = json.loads(self.excluded_products)
                    if any(pid in excluded_products for pid in product_ids):
                        return False, "Coupon cannot be applied to some products in cart"
                except:
                    pass
            
            # Check applicable products
            if self.applicable_products:
                try:
                    applicable_products = json.loads(self.applicable_products)
                    if not any(pid in applicable_products for pid in product_ids):
                        return False, "Coupon is not applicable to products in cart"
                except:
                    pass
        
        return True, "Valid"
    
    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order amount"""
        if self.discount_type == 'percentage':
            discount = (order_amount * self.discount_value) / 100
            if self.maximum_discount and discount > self.maximum_discount:
                discount = self.maximum_discount
        else:  # fixed_amount
            discount = self.discount_value
        
        return min(discount, order_amount)  # Don't discount more than order amount
    
    def use_coupon(self):
        """Mark coupon as used (increment usage count)"""
        self.used_count += 1
        db.session.commit()
    
    @staticmethod
    def validate_coupon_code(code, user_id=None, order_amount=0, product_ids=None):
        """Validate coupon code and return coupon if valid"""
        coupon = Coupon.query.filter_by(code=code, is_active=True).first()
        if not coupon:
            return None, "Invalid coupon code"
        
        is_valid, message = coupon.is_valid(user_id, order_amount, product_ids)
        if not is_valid:
            return None, message
        
        return coupon, "Valid"
