from datetime import datetime
from database import db

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
    status = db.Column(db.String(20), default='inactive')
    
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
    def _apply_active_filters(query):
        """Apply active/status filters to an Ads query"""
        active_clauses = []

        status_attr = getattr(Ads, 'status', None)
        if status_attr is not None:
            active_clauses.append(status_attr == 'active')

        if hasattr(Ads, 'is_active'):
            active_clauses.append(Ads.is_active.is_(True))

        if active_clauses:
            query = query.filter(db.or_(*active_clauses))

        return query

    @staticmethod
    def get_active_ads_by_position(position):
        """Get active ads by exact position"""
        return Ads.get_active_ads_by_positions([position])

    @staticmethod
    def get_active_ads_by_positions(positions=None):
        """Get active ads filtered by a collection of positions"""
        now = datetime.utcnow()
        query = Ads.query

        if positions:
            query = query.filter(Ads.position.in_(positions))

        query = Ads._apply_active_filters(query)

        query = query.filter(
            db.or_(Ads.start_date.is_(None), Ads.start_date <= now),
            db.or_(Ads.end_date.is_(None), Ads.end_date >= now)
        )

        return query.order_by(Ads.sort_order, Ads.created_at.desc()).all()

    @staticmethod
    def get_homepage_banners():
        """Get homepage banner ads across common position aliases"""
        home_positions = ['homepage_banner', 'homepage-hero', 'home_banner', 'homepage', 'home-hero']
        now = datetime.utcnow()

        base_query = Ads.query.filter(
            db.or_(
                Ads.position.in_(home_positions),
                Ads.position.ilike('home%'),
                Ads.position.ilike('%banner%')
            )
        )

        active_query = Ads._apply_active_filters(base_query)

        image_query = active_query.filter(
            db.or_(Ads.desktop_image.isnot(None), Ads.mobile_image.isnot(None))
        )

        time_filtered_query = image_query.filter(
            db.or_(Ads.start_date.is_(None), Ads.start_date <= now),
            db.or_(Ads.end_date.is_(None), Ads.end_date >= now)
        )

        banners = time_filtered_query.order_by(Ads.sort_order, Ads.created_at.desc()).all()
        if banners:
            return banners

        # If all ads are outside the scheduled window, fall back to active ones
        return image_query.order_by(Ads.sort_order, Ads.created_at.desc()).all()

    @staticmethod
    def get_sidebar_ads():
        """Get sidebar ads"""
        return Ads.get_active_ads_by_position('sidebar')

    @staticmethod
    def get_footer_ads():
        """Get footer ads"""
        return Ads.get_active_ads_by_position('footer')

