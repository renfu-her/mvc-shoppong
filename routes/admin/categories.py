
from flask import flash, redirect, render_template, request, url_for

from app import db
from models import Category
from utils.helpers import generate_slug

from . import admin_bp, admin_required


@admin_bp.route('/categories')
@admin_required
def categories():
    """Categories list."""
    categories_data = Category.get_three_level_categories()
    return render_template('admin/categories/list.html', categories=categories_data)


@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@admin_required
def create_category():
    """Create new category."""
    if request.method == 'POST':
        try:
            category = Category(
                name=request.form['name'],
                slug=generate_slug(request.form['name']),
                description=request.form.get('description', ''),
                parent_id=int(request.form['parent_id'])
                if request.form.get('parent_id')
                else None,
                is_parent=bool(request.form.get('is_parent')),
                sort_order=int(request.form.get('sort_order', 0)),
                is_active=bool(request.form.get('is_active')),
            )

            db.session.add(category)
            db.session.commit()
            flash('Category created successfully', 'success')
            return redirect(url_for('admin.categories'))

        except Exception as exc:
            db.session.rollback()
            flash(f'Error creating category: {exc}', 'error')

    categories = Category.query.filter_by(is_active=True).all()
    return render_template('admin/categories/create.html', categories=categories)
