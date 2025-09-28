
import os

from flask import current_app, flash, redirect, render_template, request, url_for

from app import db
from models import Category, Product
from models.product import ProductImage
from utils.helpers import generate_slug, paginate_query
from utils.image_utils import delete_image, process_product_image

from . import admin_bp, admin_required


@admin_bp.route('/products')
@admin_required
def products():
    """Products list."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', '')

    query = Product.query

    if search:
        query = query.filter(Product.name.contains(search))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)

    products_paginated = paginate_query(
        query.order_by(Product.created_at.desc()), page, 20
    )
    categories = Category.query.filter_by(is_active=True).all()

    return render_template(
        'admin/products/list.html',
        products=products_paginated,
        categories=categories,
    )


@admin_bp.route('/products/create', methods=['GET', 'POST'])
@admin_required
def create_product():
    """Create new product."""
    if request.method == 'POST':
        try:
            product = Product(
                name=request.form['name'],
                slug=generate_slug(request.form['name']),
                description=request.form.get('description', ''),
                short_description=request.form.get('short_description', ''),
                sku=request.form['sku'],
                regular_price=float(request.form['regular_price']),
                sale_price=float(request.form['sale_price'])
                if request.form.get('sale_price')
                else None,
                stock_quantity=int(request.form.get('stock_quantity', 0)),
                manage_stock=bool(request.form.get('manage_stock')),
                category_id=int(request.form['category_id']),
                status=request.form.get('status', 'draft'),
                featured=bool(request.form.get('featured')),
                is_active=bool(request.form.get('is_active')),
            )

            db.session.add(product)
            db.session.flush()

            if 'images' in request.files:
                files = request.files.getlist('images')
                for index, file in enumerate(files):
                    if file and file.filename:
                        image_path, error = process_product_image(
                            file, product.id, index == 0, index
                        )
                        if image_path:
                            db.session.add(
                                ProductImage(
                                    product_id=product.id,
                                    image_path=image_path,
                                    is_primary=(index == 0),
                                    sort_order=index,
                                )
                            )

            db.session.commit()
            flash('Product created successfully', 'success')
            return redirect(url_for('admin.products'))

        except Exception as exc:
            db.session.rollback()
            flash(f'Error creating product: {exc}', 'error')

    categories = Category.query.filter_by(is_active=True).all()
    return render_template('admin/products/create.html', categories=categories)


@admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    """Edit product."""
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        try:
            product.name = request.form['name']
            product.slug = generate_slug(request.form['name'])
            product.description = request.form.get('description', '')
            product.short_description = request.form.get('short_description', '')
            product.sku = request.form['sku']
            product.regular_price = float(request.form['regular_price'])
            product.sale_price = (
                float(request.form['sale_price'])
                if request.form.get('sale_price')
                else None
            )
            product.stock_quantity = int(request.form.get('stock_quantity', 0))
            product.manage_stock = bool(request.form.get('manage_stock'))
            product.category_id = int(request.form['category_id'])
            product.status = request.form.get('status', 'draft')
            product.featured = bool(request.form.get('featured'))
            product.is_active = bool(request.form.get('is_active'))

            if 'images' in request.files:
                files = request.files.getlist('images')
                for index, file in enumerate(files):
                    if file and file.filename:
                        image_path, error = process_product_image(
                            file,
                            product.id,
                            False,
                            len(product.images) + index,
                        )
                        if image_path:
                            db.session.add(
                                ProductImage(
                                    product_id=product.id,
                                    image_path=image_path,
                                    is_primary=False,
                                    sort_order=len(product.images) + index,
                                )
                            )

            db.session.commit()
            flash('Product updated successfully', 'success')
            return redirect(url_for('admin.products'))

        except Exception as exc:
            db.session.rollback()
            flash(f'Error updating product: {exc}', 'error')

    categories = Category.query.filter_by(is_active=True).all()
    return render_template(
        'admin/products/edit.html',
        product=product,
        categories=categories,
    )


@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@admin_required
def delete_product(id):
    """Delete a product."""
    product = Product.query.get_or_404(id)

    try:
        for image in product.images:
            if image.image_path:
                delete_image(
                    os.path.join(
                        current_app.root_path,
                        'static',
                        image.image_path.replace('/', os.sep),
                    )
                )

        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Error deleting product: {exc}', 'error')

    return redirect(url_for('admin.products'))
