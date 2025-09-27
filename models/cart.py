from datetime import datetime
from decimal import Decimal
from database import db

class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)  # For guest users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Cart {self.id}>'
    
    @property
    def total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items)
    
    @property
    def subtotal(self):
        """Calculate cart subtotal"""
        return sum(item.total_price for item in self.items)
    
    @property
    def total(self):
        """Calculate cart total (subtotal + shipping + tax - discounts)"""
        # For now, just return subtotal. Can be extended with shipping, tax, discounts
        return self.subtotal
    
    def add_item(self, product_id, quantity=1):
        """Add item to cart or update quantity if item already exists"""
        existing_item = CartItem.query.filter_by(cart_id=self.id, product_id=product_id).first()
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = CartItem(
                cart_id=self.id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(new_item)
        
        db.session.commit()
        return True
    
    def update_item_quantity(self, product_id, quantity):
        """Update item quantity in cart"""
        item = CartItem.query.filter_by(cart_id=self.id, product_id=product_id).first()
        if item:
            if quantity <= 0:
                db.session.delete(item)
            else:
                item.quantity = quantity
            db.session.commit()
            return True
        return False
    
    def remove_item(self, product_id):
        """Remove item from cart"""
        item = CartItem.query.filter_by(cart_id=self.id, product_id=product_id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            return True
        return False
    
    def clear(self):
        """Clear all items from cart"""
        for item in self.items:
            db.session.delete(item)
        db.session.commit()
    
    @staticmethod
    def get_or_create_cart(user_id=None, session_id=None):
        """Get existing cart or create new one"""
        if user_id:
            cart = Cart.query.filter_by(user_id=user_id).first()
        elif session_id:
            cart = Cart.query.filter_by(session_id=session_id).first()
        else:
            return None
        
        if not cart:
            cart = Cart(user_id=user_id, session_id=session_id)
            db.session.add(cart)
            db.session.commit()
        
        return cart

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CartItem {self.product.name} x {self.quantity}>'
    
    @property
    def unit_price(self):
        """Get current unit price of the product"""
        return self.product.current_price
    
    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        return self.unit_price * self.quantity
