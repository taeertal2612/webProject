from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
def show_inventory():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('user.login'))

    db = get_db()
    inventory = db.execute('''
        SELECT inventory.id, products.name AS product_name, inventory.quantity, inventory.min_required, inventory.updated_at
        FROM inventory JOIN products ON inventory.product_id = products.id
    ''').fetchall()
    return render_template('inventory.html', inventory=inventory)

@inventory_bp.route('/inventory/update/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return "גישה נדחתה", 403

    try:
        new_quantity = int(request.form['quantity'])
        if new_quantity < 0:
            flash('⚠️ לא ניתן להזין כמות שלילית', 'error')
            return redirect(url_for('inventory.show_inventory'))
    except ValueError:
        flash('⚠️ יש להזין מספר חוקי בלבד', 'error')
        return redirect(url_for('inventory.show_inventory'))

    db = get_db()
    db.execute('UPDATE inventory SET quantity=?, updated_at=datetime("now", "localtime") WHERE id=?', (new_quantity, item_id))
    db.commit()
    flash('✅ המלאי עודכן בהצלחה', 'success')
    return redirect(url_for('inventory.show_inventory'))
