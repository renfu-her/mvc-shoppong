from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from database import db
import os

migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'frontend.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Import models to register them with SQLAlchemy
    from models import User, Category, Product, ProductImage, Cart, CartItem, Ads, Coupon, ShippingFee, WishList
    from models.order import Order, OrderItem
    
    # Create upload directories
    os.makedirs('static/uploads/products', exist_ok=True)
    os.makedirs('static/uploads/ads', exist_ok=True)
    
    # Register blueprints
    from routes.frontend import frontend_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(frontend_bp)
    app.register_blueprint(admin_bp, url_prefix='/backend')
    app.register_blueprint(api_bp, url_prefix='/api')

    register_cli_commands(app)
    
    return app


def register_cli_commands(app):
    from flask.cli import with_appcontext
    import click
    from tasks.order_status import sync_pending_orders

    @app.cli.command('sync-pending-orders')
    @click.option('--limit', default=50, show_default=True, help='Maximum pending orders to query per run')
    @with_appcontext
    def sync_pending_orders_command(limit):
        updated = sync_pending_orders(limit=limit)
        click.echo(f'Synced {updated} pending orders.')


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
