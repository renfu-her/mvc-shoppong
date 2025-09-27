from datetime import datetime
from decimal import Decimal
from database import db

class ShippingFee(db.Model):
    __tablename__ = 'shipping_fees'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Shipping method details
    method_type = db.Column(db.String(50), nullable=False)  # flat_rate, free_shipping, weight_based, price_based
    cost = db.Column(db.Numeric(10, 2), default=0)
    
    # Conditions for free shipping
    free_shipping_threshold = db.Column(db.Numeric(10, 2), nullable=True)  # Minimum order amount for free shipping
    
    # Weight-based shipping
    min_weight = db.Column(db.Numeric(8, 2), nullable=True)
    max_weight = db.Column(db.Numeric(8, 2), nullable=True)
    weight_cost = db.Column(db.Numeric(10, 2), nullable=True)  # Cost per unit weight
    
    # Price-based shipping
    min_order_amount = db.Column(db.Numeric(10, 2), nullable=True)
    max_order_amount = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Geographic restrictions
    applicable_countries = db.Column(db.Text, nullable=True)  # JSON array of country codes
    applicable_states = db.Column(db.Text, nullable=True)  # JSON array of state codes
    excluded_countries = db.Column(db.Text, nullable=True)  # JSON array of country codes
    excluded_states = db.Column(db.Text, nullable=True)  # JSON array of state codes
    
    # Delivery time
    estimated_days_min = db.Column(db.Integer, nullable=True)
    estimated_days_max = db.Column(db.Integer, nullable=True)
    
    # Status and ordering
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ShippingFee {self.name}>'
    
    def calculate_shipping_cost(self, order_amount=0, total_weight=0, country=None, state=None):
        """Calculate shipping cost based on order details"""
        
        # Check if shipping method is active
        if not self.is_active:
            return None
        
        # Check geographic restrictions
        if country:
            import json
            
            # Check excluded countries
            if self.excluded_countries:
                try:
                    excluded_countries = json.loads(self.excluded_countries)
                    if country in excluded_countries:
                        return None
                except:
                    pass
            
            # Check applicable countries
            if self.applicable_countries:
                try:
                    applicable_countries = json.loads(self.applicable_countries)
                    if country not in applicable_countries:
                        return None
                except:
                    pass
            
            # Check state restrictions
            if state and self.applicable_states:
                try:
                    applicable_states = json.loads(self.applicable_states)
                    if state not in applicable_states:
                        return None
                except:
                    pass
            
            if state and self.excluded_states:
                try:
                    excluded_states = json.loads(self.excluded_states)
                    if state in excluded_states:
                        return None
                except:
                    pass
        
        # Calculate cost based on method type
        if self.method_type == 'flat_rate':
            return self.cost
        
        elif self.method_type == 'free_shipping':
            if self.free_shipping_threshold and order_amount >= self.free_shipping_threshold:
                return 0
            return self.cost
        
        elif self.method_type == 'weight_based':
            if self.min_weight and total_weight < self.min_weight:
                return None
            if self.max_weight and total_weight > self.max_weight:
                return None
            if self.weight_cost:
                return total_weight * self.weight_cost
            return self.cost
        
        elif self.method_type == 'price_based':
            if self.min_order_amount and order_amount < self.min_order_amount:
                return None
            if self.max_order_amount and order_amount > self.max_order_amount:
                return None
            return self.cost
        
        return self.cost
    
    def get_estimated_delivery(self):
        """Get estimated delivery time as string"""
        if self.estimated_days_min and self.estimated_days_max:
            if self.estimated_days_min == self.estimated_days_max:
                return f"{self.estimated_days_min} days"
            else:
                return f"{self.estimated_days_min}-{self.estimated_days_max} days"
        elif self.estimated_days_min:
            return f"{self.estimated_days_min}+ days"
        return "Standard delivery"
    
    @staticmethod
    def get_available_shipping_methods(order_amount=0, total_weight=0, country=None, state=None):
        """Get all available shipping methods for given order details"""
        methods = ShippingFee.query.filter_by(is_active=True).order_by(ShippingFee.sort_order).all()
        available_methods = []
        
        for method in methods:
            cost = method.calculate_shipping_cost(order_amount, total_weight, country, state)
            if cost is not None:
                available_methods.append({
                    'method': method,
                    'cost': cost,
                    'estimated_delivery': method.get_estimated_delivery()
                })
        
        return available_methods
    
    @staticmethod
    def get_free_shipping_threshold():
        """Get the minimum order amount for free shipping"""
        free_shipping = ShippingFee.query.filter_by(
            method_type='free_shipping',
            is_active=True
        ).first()
        
        if free_shipping and free_shipping.free_shipping_threshold:
            return free_shipping.free_shipping_threshold
        
        return None
