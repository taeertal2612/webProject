import os
from flask import Flask, request, g, render_template, redirect, url_for, flash, session
import sqlite3
import click


# Ensure the 'database' folder exists before using it
if not os.path.exists('database'):
    os.makedirs('database')

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # נדרש לניהול session
DATABASE = 'database/people.db'

# --- Database Helper Functions ---

def get_db(): # פותח חיבור למסד נתונים
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    
    # טבלת קטגוריות
    db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    # הוספת קטגוריות אם הן לא קיימות
    db.executemany('''
    INSERT OR IGNORE INTO categories (id, name)
    VALUES (?, ?)
    ''', [
    (1, 'fresh beef'),
    (2, 'fresh chicken'),
    (3, 'frozen chicken'),
    (4, 'sausages'),
    (5, 'processed'),
    (6, 'offal')
    ])
    
    # טבלת מוצרים
    db.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category_id INTEGER,
            description TEXT,
            image_url TEXT,
            on_sale INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # טבלת מלאי
    db.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            min_required INTEGER DEFAULT 10,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # טבלת לקוחות
    db.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL
        )
    ''')

    # טבלת מנהלים ומשתמשים
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'client')) NOT NULL
        )
    ''')
    db.execute('''
    INSERT or IGNORE INTO users (id, username, password, role)
    VALUES (?, ?, ?, ?)
''', (1, 'manager', '1234', 'admin'))
    
     # סנכרון מוצרים קיימים אל טבלת המלאי
    product_ids = db.execute('SELECT id FROM products').fetchall()
    for product in product_ids:
        db.execute('''
            INSERT OR IGNORE INTO inventory (product_id, quantity)
            VALUES (?, ?)
        ''', (product['id'], 0))
    db.commit()


# --- Routes ---
#פעולות שהן למעשה הנתיב למערכת שלנו - דרכו פלאסק יודע מה להציג, מה לשלוף מהמסד נתונים, כשמישהו לוחץ על כפתור למשל
@app.route('/') #עמוד הבית 
def home():
    return render_template('index.html')
#---------קטלוג המוצרים---------
# הצגת כל קטלוג המוצרים
@app.route('/katalog')
def show_katalog():
    db = get_db()
    cur = db.execute('''
        SELECT products.id, products.name, products.price, categories.name AS category
        FROM products
        LEFT JOIN categories ON products.category_id = categories.id
    ''')
    products = cur.fetchall()
    return render_template('katalog.html', products=products)

# הוספת מוצר חדש (GET - טופס, POST - שליחה)
@app.route('/katalog/new', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        return "גישה נדחתה – רק מנהלים יכולים להוסיף מוצרים", 403

    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category_id = request.form['category']
        description = request.form['description']
        image_url = request.form['image_url']

        db.execute('''
            INSERT INTO products (name, price, category_id, description, image_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, price, category_id, description, image_url))
        db.commit()
        return redirect(url_for('show_katalog'))

    categories = db.execute('SELECT * FROM categories').fetchall()
    return render_template('add_product.html', categories=categories)

#---------בקרות מלאי--------
# הצגת מלאי
@app.route('/inventory')
def show_inventory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        return "אין לך הרשאה לצפות בדף זה", 403

    db = get_db()
    inventory = db.execute('''
        SELECT inventory.id, products.name AS product_name, inventory.quantity, inventory.min_required
        FROM inventory
        JOIN products ON inventory.product_id = products.id
    ''').fetchall()
    return render_template('inventory.html', inventory=inventory)

# עדכון כמות מוצר במלאי (POST)
@app.route('/inventory/update/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return "גישה נדחתה", 403

    new_quantity = request.form['quantity']
    db = get_db()
    db.execute('UPDATE inventory SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_quantity, item_id))
    db.commit()
    return redirect(url_for('show_inventory'))

#---------ניהול לקוחות---------
# צפייה בפרופיל לקוח
@app.route('/client/profile')
def client_profile():
    if 'client_id' not in session:
        return redirect(url_for('client_register'))
    db = get_db()
    cur = db.execute('SELECT * FROM clients WHERE id = ?', (session['client_id'],))
    client = cur.fetchone()
    return render_template('client_profile.html', client=client)

# הרשמה של לקוח חדש
@app.route('/client/register', methods=['GET', 'POST'])
def client_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        db = get_db()
        try:
            # הוספת לקוח
            db.execute('INSERT INTO clients (name, email, phone, password) VALUES (?, ?, ?, ?)',
                       (name, email, phone, password))
            
            # הוספתו גם לטבלת users כמשתמש רגיל (client)
            db.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
                       (email, password, 'client'))
            
            db.commit()
            flash('ההרשמה בוצעה בהצלחה, אנא התחבר')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('האימייל כבר קיים במערכת')
    return render_template('client_register.html')

# עריכת פרטי לקוח
@app.route('/client/edit', methods=['GET', 'POST'])
def client_edit():
    if 'client_id' not in session:
        return redirect(url_for('client_register'))
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        if password:
            db.execute('UPDATE clients SET name=?, email=?, phone=?, password=? WHERE id=?',
                       (name, email, phone, password, session['client_id']))
        else:
            db.execute('UPDATE clients SET name=?, email=?, phone=? WHERE id=?',
                       (name, email, phone, session['client_id']))
        db.commit()
        flash('הפרטים עודכנו בהצלחה')
        return redirect(url_for('client_profile'))

    cur = db.execute('SELECT * FROM clients WHERE id = ?', (session['client_id'],))
    client = cur.fetchone()
    return render_template('client_edit.html', client=client)

# מחיקת חשבון לקוח
@app.route('/client/delete', methods=['GET', 'POST'])
def client_delete():
    if 'client_id' not in session:
        return redirect(url_for('client_register'))
    if request.method == 'POST':
        db = get_db()
        db.execute('DELETE FROM clients WHERE id = ?', (session['client_id'],))
        db.commit()
        session.clear()
        flash('החשבון נמחק בהצלחה')
        return redirect(url_for('client_register'))
    return render_template('client_delete.html')

#---------התחברות-----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('שם משתמש או סיסמה שגויים')
    return render_template('login.html')

@app.route('/dashboard') # לאחר התחברות, המשתמש מועבר לדשבורד
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'], role=session['role'])

@app.route('/client/login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cur = db.execute('SELECT * FROM clients WHERE email = ? AND password = ?', (email, password))
        client = cur.fetchone()

        if client:
            session['client_id'] = client['id']
            session['client_name'] = client['name']
            flash('התחברת בהצלחה!')
            return redirect(url_for('client_profile'))
        else:
            flash('אימייל או סיסמה שגויים')

    return render_template('client_login.html')
@app.route('/client/logout')
def client_logout():
    session.pop('client_id', None)
    session.pop('client_name', None)
    flash('התנתקת בהצלחה')
    return redirect(url_for('client_login'))

@app.route('/logout')#התנתקות
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)