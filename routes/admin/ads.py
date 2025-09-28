
import os

from flask import current_app, flash, redirect, render_template, request, url_for

from app import db
from models import Ads
from utils.image_utils import delete_image, process_ad_image

from . import admin_bp, admin_required


@admin_bp.route('/ads')
@admin_required
def ads():
    """Ads list."""
    ads_items = Ads.query.order_by(Ads.created_at.desc()).all()
    return render_template('admin/ads/list.html', ads=ads_items)


@admin_bp.route('/ads/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_ad(id):
    """Edit advertisement."""
    ad = Ads.query.get_or_404(id)

    if request.method == 'POST':
        ad.title = request.form['title']
        ad.description = request.form.get('description', '')
        ad.link_url = request.form.get('link_url', '')
        ad.position = request.form['position']
        ad.sort_order = int(request.form.get('sort_order', 0))
        ad.is_active = bool(request.form.get('is_active'))

        try:
            ad.status = 'active' if ad.is_active else 'inactive'
        except Exception:
            pass

        try:
            desktop_file = request.files.get('desktop_image')
            mobile_file = request.files.get('mobile_image')

            if request.form.get('remove_desktop_image') and ad.desktop_image:
                delete_image(
                    os.path.join(
                        current_app.root_path,
                        'static',
                        ad.desktop_image.replace('/', os.sep),
                    )
                )
                ad.desktop_image = None
            elif desktop_file and desktop_file.filename:
                if ad.desktop_image:
                    delete_image(
                        os.path.join(
                            current_app.root_path,
                            'static',
                            ad.desktop_image.replace('/', os.sep),
                        )
                    )
                desktop_path, error = process_ad_image(desktop_file, ad.id, 'desktop')
                if error or not desktop_path:
                    raise ValueError(error or 'Failed to process desktop image')
                ad.desktop_image = desktop_path

            if request.form.get('remove_mobile_image') and ad.mobile_image:
                delete_image(
                    os.path.join(
                        current_app.root_path,
                        'static',
                        ad.mobile_image.replace('/', os.sep),
                    )
                )
                ad.mobile_image = None
            elif mobile_file and mobile_file.filename:
                if ad.mobile_image:
                    delete_image(
                        os.path.join(
                            current_app.root_path,
                            'static',
                            ad.mobile_image.replace('/', os.sep),
                        )
                    )
                mobile_path, error = process_ad_image(mobile_file, ad.id, 'mobile')
                if error or not mobile_path:
                    raise ValueError(error or 'Failed to process mobile image')
                ad.mobile_image = mobile_path

            db.session.commit()
            flash('Advertisement updated successfully', 'success')
            return redirect(url_for('admin.ads'))
        except ValueError as err:
            db.session.rollback()
            flash(str(err), 'error')
        except Exception as exc:
            db.session.rollback()
            flash(f'Error updating advertisement: {exc}', 'error')

    return render_template('admin/ads/edit.html', ad=ad)


@admin_bp.route('/ads/<int:id>/delete', methods=['POST'])
@admin_required
def delete_ad(id):
    """Delete advertisement."""
    ad = Ads.query.get_or_404(id)

    try:
        if ad.desktop_image:
            delete_image(
                os.path.join(
                    current_app.root_path,
                    'static',
                    ad.desktop_image.replace('/', os.sep),
                )
            )
        if ad.mobile_image:
            delete_image(
                os.path.join(
                    current_app.root_path,
                    'static',
                    ad.mobile_image.replace('/', os.sep),
                )
            )

        db.session.delete(ad)
        db.session.commit()
        flash('Advertisement deleted successfully', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Error deleting advertisement: {exc}', 'error')

    return redirect(url_for('admin.ads'))


@admin_bp.route('/ads/create', methods=['GET', 'POST'])
@admin_required
def create_ad():
    """Create new ad."""
    if request.method == 'POST':
        try:
            ad = Ads(
                title=request.form['title'],
                description=request.form.get('description', ''),
                link_url=request.form.get('link_url', ''),
                position=request.form['position'],
                sort_order=int(request.form.get('sort_order', 0)),
                is_active=bool(request.form.get('is_active')),
            )

            try:
                ad.status = 'active' if ad.is_active else 'inactive'
            except Exception:
                pass

            db.session.add(ad)
            db.session.flush()

            if 'desktop_image' in request.files:
                file = request.files['desktop_image']
                if file and file.filename:
                    image_path, error = process_ad_image(file, ad.id, 'desktop')
                    if image_path:
                        ad.desktop_image = image_path

            if 'mobile_image' in request.files:
                file = request.files['mobile_image']
                if file and file.filename:
                    image_path, error = process_ad_image(file, ad.id, 'mobile')
                    if image_path:
                        ad.mobile_image = image_path

            db.session.commit()
            flash('Advertisement created successfully', 'success')
            return redirect(url_for('admin.ads'))

        except Exception as exc:
            db.session.rollback()
            flash(f'Error creating advertisement: {exc}', 'error')

    return render_template('admin/ads/create.html')
