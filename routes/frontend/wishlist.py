
from flask import render_template
from flask_login import login_required, current_user

from models import WishList

from . import frontend_bp


@frontend_bp.route('/wishlist')
@login_required
def wishlist():
    """Display the current user's wishlist."""
    items = (
        WishList.query.filter_by(user_id=current_user.id)
        .order_by(WishList.created_at.desc())
        .all()
    )
    return render_template('frontend/wishlist.html', items=items)
