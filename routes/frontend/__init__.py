from flask import Blueprint

frontend_bp = Blueprint('frontend', __name__)

# Import route modules so they register with the blueprint
from . import auth, catalog, wishlist, cart, account, api  # noqa: F401

__all__ = ['frontend_bp']
