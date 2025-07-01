from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db
from utils.helpers import save_uploaded_image, allowed_file
from werkzeug.utils import secure_filename
import os

product_bp = Blueprint('product', __name__)

@product_bp.route('/katalog')
def show_katalog():
    db = get_db()
    products = db.execute('''
        SELECT products.id, products.name, products.price, products.description, products.image_url, products.on_sale, categories.name AS category
        FROM products LEFT JOIN categories ON products.category_id = categories.id
    ''').fetchall()
    deals_raw = db.execute('SELECT name FROM deals').fetchall()
    deal_names = [row['name'] for row in deals_raw]
    return render_template('katalog.html', products=products, deal_names=deal_names)

@product_bp.route('/katalog/new', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('user.login'))

    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category_id = request.form['category']
        description = request.form['description']
        image_url_input = request.form.get('image_url', '').strip()
        image_file = request.files.get('image_file')
        final_image_url = save_uploaded_image(image_file) or image_url_input

        cur = db.execute('''
            INSERT INTO products (name, price, category_id, description, image_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, price, category_id, description, final_image_url))

        product_id = cur.lastrowid
        db.execute('INSERT INTO inventory (product_id, quantity) VALUES (?, 0)', (product_id,))
        db.commit()
        flash('המוצר נוסף בהצלחה ונרשם למלאי בכמות 0')
        return redirect(url_for('product.show_katalog'))

    categories = db.execute('SELECT * FROM categories').fetchall()
    return render_template('katalog_form.html', categories=categories, product=None)

@product_bp.route('/katalog/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('user.login'))

    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category_id = request.form['category']
        description = request.form['description']
        image_url_input = request.form.get('image_url', '').strip()
        image_file = request.files.get('image_file')
        final_image_url = save_uploaded_image(image_file) if image_file else image_url_input

        db.execute('''
            UPDATE products
            SET name=?, price=?, category_id=?, description=?, image_url=?, updated_at=datetime('now', 'localtime')
            WHERE id=?
        ''', (name, price, category_id, description, final_image_url, product_id))
        db.commit()
        return redirect(url_for('product.show_katalog'))

    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    categories = db.execute('SELECT * FROM categories').fetchall()
    return render_template('katalog_form.html', product=product, categories=categories)
