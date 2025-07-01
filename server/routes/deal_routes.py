from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db
from utils.helpers import save_uploaded_image, allowed_file

deal_bp = Blueprint('deal', __name__)

@deal_bp.route('/deals')
def show_deals():
    db = get_db()
    deals = db.execute("SELECT * FROM deals").fetchall()
    return render_template('deals.html', deals=deals)

@deal_bp.route('/add_deal', methods=['GET', 'POST'])
def add_deal():
    if not session.get('user_id') or session.get('role') != 'admin':
        flash("רק מנהלים יכולים להוסיף מבצעים.")
        return redirect(url_for('deal.show_deals'))

    if request.method == 'POST':
        name = request.form['name']
        image_file = request.files.get('image_file')
        image_url_input = request.form.get('image_url', '').strip()
        original_price = float(request.form['original_price'])
        discounted_price = float(request.form['discounted_price'])
        description = request.form['description']
        final_image_url = save_uploaded_image(image_file) or image_url_input

        db = get_db()
        db.execute('''
            INSERT INTO deals (name, image_url, original_price, discounted_price, description, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
        ''', (name, final_image_url, original_price, discounted_price, description))
        db.commit()
        flash("מבצע נוסף!")
        return redirect(url_for('deal.show_deals'))

    return render_template('add_deal.html')
