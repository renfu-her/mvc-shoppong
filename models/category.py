from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    is_parent = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for hierarchical categories
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def get_level(self):
        """Get the level of the category in the hierarchy (0 for root)"""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level
    
    def get_ancestors(self):
        """Get all ancestor categories"""
        ancestors = []
        parent = self.parent
        while parent:
            ancestors.append(parent)
            parent = parent.parent
        return ancestors
    
    def get_descendants(self):
        """Get all descendant categories"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    @staticmethod
    def get_root_categories():
        """Get all root categories (is_parent = True)"""
        return Category.query.filter_by(is_parent=True, is_active=True).order_by(Category.sort_order).all()
    
    @staticmethod
    def get_three_level_categories():
        """Get categories organized in three levels"""
        root_categories = Category.get_root_categories()
        result = []
        
        for root in root_categories:
            root_data = {
                'category': root,
                'children': []
            }
            
            for child in root.children:
                if child.is_active:
                    child_data = {
                        'category': child,
                        'children': [grandchild for grandchild in child.children if grandchild.is_active]
                    }
                    root_data['children'].append(child_data)
            
            result.append(root_data)
        
        return result
