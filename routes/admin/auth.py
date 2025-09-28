
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from models import User

from . import admin_bp


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_admin:
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid credentials', 'error')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout."""
    logout_user()
    return redirect(url_for('admin.login'))
