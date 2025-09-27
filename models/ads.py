from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db

class Ads(db.Model):
    __tablename__ = 'ads'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Image paths for different device types
    desktop_image = db.Column(db.String(255), nullable=True)  # 16:9 aspect ratio
    mobile_image = db.Column(db.String(255), nullable=True)   # 9:16 aspect ratio
    
    # Link and target
    link_url = db.Column(db.String(500), nullable=True)
    link_target = db.Column(db.String(20), default='_self')  # _self, _blank
    
    # Display settings
    position = db.Column(db.String(50), nullable=False)  # homepage_banner, sidebar, footer, etc.
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Date range
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    
    # Click tracking
    click_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Ads {self.title}>'
    
    def is_currently_active(self):
        """Check if ad is currently active based on date range"""
        now = datetime.utcnow()
        
        if not self.is_active:
            return False
        
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        db.session.commit()
    
    def increment_click_count(self):
        """Increment click count"""
        self.click_count += 1
        db.session.commit()
    
    @staticmethod
    def get_active_ads_by_position(position):
        """Get active ads by position"""
        now = datetime.utcnow()
        return Ads.query.filter(
            Ads.position == position,
            Ads.is_active == True,
            db.or_(Ads.start_date.is_(None), Ads.start_date <= now),
            db.or_(Ads.end_date.is_(None), Ads.end_date >= now)
        ).order_by(Ads.sort_order).all()
    
    @staticmethod
    def get_homepage_banners():
        """Get homepage banner ads"""
        return Ads.get_active_ads_by_position('homepage_banner')
    
    @staticmethod
    def get_sidebar_ads():
        """Get sidebar ads"""
        return Ads.get_active_ads_by_position('sidebar')
    
    @staticmethod
    def get_footer_ads():
        """Get footer ads"""
        return Ads.get_active_ads_by_position('footer')
