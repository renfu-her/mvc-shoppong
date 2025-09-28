
from functools import wraps

from flask import Blueprint, flash, redirect, url_for
from flask_login import current_user

admin_bp = Blueprint('admin', __name__)


def admin_required(func):
    """Decorator to require admin access."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('admin.login'))
        return func(*args, **kwargs)

    return decorated_function


# Import route modules so they register their views
from . import auth, dashboard, products, categories, orders, ads, coupons, shipping  # noqa: F401

__all__ = ['admin_bp', 'admin_required']
