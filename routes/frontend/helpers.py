from __future__ import annotations

import uuid
from flask import session
from flask_login import current_user

from models import Cart, WishList


def get_or_create_cart():
    '''Return the cart for the current user or anonymous session.'''
    if current_user.is_authenticated:
        cart = Cart.get_or_create_cart(user_id=current_user.id)
    else:
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        cart = Cart.get_or_create_cart(session_id=session_id)
    return cart


def get_user_wishlist_product_ids():
    '''Return a set of product ids that belong to the active user's wishlist.'''
    if current_user.is_authenticated:
        return {item.product_id for item in WishList.query.filter_by(user_id=current_user.id)}
    return set()


def get_wishlist_count():
    '''Return the wishlist item count for the active user.'''
    if current_user.is_authenticated:
        return WishList.query.filter_by(user_id=current_user.id).count()
    return 0
