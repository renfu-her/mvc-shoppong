from datetime import datetime
from decimal import Decimal
from database import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    short_description = db.Column(db.Text, nullable=True)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    
    # Pricing
    regular_price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Inventory
    stock_quantity = db.Column(db.Integer, default=0)
    manage_stock = db.Column(db.Boolean, default=True)
    stock_status = db.Column(db.String(20), default='instock')  # instock, outofstock
    
    # Product details
    weight = db.Column(db.Numeric(8, 2), nullable=True)
    dimensions = db.Column(db.String(100), nullable=True)  # LxWxH
    color = db.Column(db.String(50), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    material = db.Column(db.String(100), nullable=True)
    
    # SEO
    meta_title = db.Column(db.String(200), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)
    
    # Status and visibility
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    @property
    def current_price(self):
        """Get the current price (sale price if available, otherwise regular price)"""
        return self.sale_price if self.sale_price else self.regular_price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.sale_price and self.regular_price:
            return round(((self.regular_price - self.sale_price) / self.regular_price) * 100)
        return 0
    
    @property
    def is_on_sale(self):
        """Check if product is on sale"""
        return self.sale_price is not None and self.sale_price < self.regular_price
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        if not self.manage_stock:
            return self.stock_status == 'instock'
        return self.stock_quantity > 0
    
    def get_primary_image(self):
        """Get the primary product image"""
        primary_image = ProductImage.query.filter_by(product_id=self.id, is_primary=True).first()
        if not primary_image:
            primary_image = ProductImage.query.filter_by(product_id=self.id).first()
        return primary_image
    
    def get_all_images(self):
        """Get all product images ordered by sort_order"""
        return ProductImage.query.filter_by(product_id=self.id).order_by(ProductImage.sort_order).all()
    
    @staticmethod
    def get_featured_products(limit=8):
        """Get featured products"""
        return Product.query.filter_by(featured=True, is_active=True, status='published').limit(limit).all()
    
    @staticmethod
    def get_new_arrivals(limit=8):
        """Get new arrival products"""
        return Product.query.filter_by(is_active=True, status='published').order_by(Product.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_best_sellers(limit=8):
        """Get best selling products based on order items"""
        from models.order import OrderItem
        return db.session.query(Product).join(OrderItem).filter(
            Product.is_active == True,
            Product.status == 'published'
        ).group_by(Product.id).order_by(db.func.sum(OrderItem.quantity).desc()).limit(limit).all()
    
    @staticmethod
    def get_on_sale_products(limit=8):
        """Get products on sale"""
        return Product.query.filter(
            Product.sale_price.isnot(None),
            Product.sale_price < Product.regular_price,
            Product.is_active == True,
            Product.status == 'published'
        ).limit(limit).all()

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(200), nullable=True)
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductImage {self.image_path}>'
