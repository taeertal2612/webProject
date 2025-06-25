import os
from flask import Flask, request, g, render_template, redirect, url_for, flash, session
import sqlite3
import re
from werkzeug.utils import secure_filename
from ai_ollama import run_ai_assistant


# Ensure the 'database' folder exists before using it
if not os.path.exists('database'):
    os.makedirs('database')

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # נדרש לניהול session
DATABASE = 'database/people.db'

# הגדרות
IMAGE_FOLDER = 'static/images'
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'avif'}

def save_uploaded_image(image_file):
    """שומר תמונה בתיקייה static/images ומחזיר את הנתיב היחסי לתצוגה"""
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        save_dir = app.config['IMAGE_FOLDER']
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        image_file.save(save_path)
        return '/static/images/' + filename
    return ''

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




# --- Database Helper Functions ---

def get_db(): # פותח חיבור למסד נתונים
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close() 
def init_db():
    db = get_db()

    # יצירת טבלת קטגוריות
    db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # הוספת קטגוריות
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

    # יצירת טבלת מוצרים
    db.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            category_id INTEGER,
            description TEXT,
            image_url TEXT,
            on_sale INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    cursor = db.cursor()

    # הכנסת מוצרים התחלתיים
    db.executemany('''
        INSERT OR IGNORE INTO products (name, price, category_id, description, image_url, on_sale)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        ('בשר טחון טרי', 45.90, 1, 'בשר בקר טחון באיכות גבוהה, מתאים לקציצות ולפסטה', 'בקר טרי טחון.avif', 0),
        ('סטייק אנטריקוט', 89.00, 1, 'נתח מובחר לסטייקים עסיסיים', 'אנטריקוט אנגוס קפוא.avif', 0),
        ('חזה עוף טרי', 34.90, 2, 'חזה עוף טרי לנגיסים, שניצל או בישול בריא', 'חזה עוף שלם טרי.avif', 0),
        ('כבד עוף', 24.00, 6, 'כבד עוף טרי, מתאים למרק או ממרח', 'כבד.avif', 0),
        ('קבב בקר מתובל', 49.00, 5, 'קבב מתובל מוכן לצלייה על האש או במחבת', 'קבב בקר.avif', 0),
        ('נקנקיות ביתיות', 39.90, 4, 'נקנקיות עוף ביתיות בעבודת יד', 'נקניקיות קפואות.avif', 0),
        ('כנפיים צלויות מוכנות', 42.00, 5, 'כנפיים מתובלות מוכנות לחימום בתנור', 'כנפיים.avif', 0),
        ('שוקיים עוף טרי', 31.00, 2, 'שוקיים טריים להכנה בתנור או על האש', 'שוקיים עוף טרי.avif', 0),
        ('שניצל עוף קפוא', 29.90, 3, 'שניצלים קפואים מוכנים לטיגון או אפייה, נוחים לארוחה מהירה', 'שניצל עוף קפוא.avif', 0)
    ])

    # עדכון תמונה למוצר שכבר קיים
    db.execute('''
        UPDATE products
        SET image_url = 'שוקיים עוף טרי.avif'
        WHERE name = 'שוקיים עוף טרי'
    ''')

# יצירת טבלת מלאי

    db.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL UNIQUE,
        quantity INTEGER NOT NULL DEFAULT 0,
        min_required INTEGER DEFAULT 10,
        updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
''')

    # סנכרון כל המוצרים אל המלאי
    product_ids = db.execute('SELECT id FROM products').fetchall()
    for product in product_ids:
        db.execute('''
            INSERT OR IGNORE INTO inventory (product_id, quantity)
            VALUES (?, ?)
        ''', (product['id'], 0))

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

    # טבלת משתמשים
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'client')) NOT NULL
        )
    ''')

    # יצירת מנהל ברירת מחדל
    db.execute('''
        INSERT OR IGNORE INTO users (id, username, password, role)
        VALUES (?, ?, ?, ?)
    ''', (1, 'manager', '1234', 'admin'))
    
    #יצירת טבלת מבצעים
    db.execute('''
            CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_url TEXT,
            original_price REAL,
            discounted_price REAL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime')))
            ''')
    cursor = db.cursor()
    cursor.execute("DELETE FROM deals")
    # הכנסת מבצעים ראשוניים
    db.executemany('''
    INSERT OR IGNORE INTO deals (id, name, image_url, original_price, discounted_price, description)
    VALUES (?, ?, ?, ?, ?, ?)''',
    [(1,'סטייק אנטריקוט', '/static/images/אנטריקוט אנגוס קפוא.avif', 89.00, 75.00, 'בשר בקר מובחר במחיר חגיגי לחברי מועדון!'),
    (2, 'חזה עוף טרי', '/static/images/חזה עוף שלם טרי.avif', 34.90, 25.00, 'חזה עוף טרי ואיכותי – רק לחברי המועדון.'),
    (3, 'קבב בקר מתובל', '/static/images/קבב בקר.avif', 89.90, 69.90, 'קבב בקר מתובל בעבודת יד – מבצע השבוע!')
    ])
    
    db.commit()


# --- Routes ---
#פעולות שהן למעשה הנתיב למערכת שלנו - דרכו פלאסק יודע מה להציג, מה לשלוף מהמסד נתונים, כשמישהו לוחץ על כפתור למשל
@app.route('/') #עמוד הבית 
def home():
    return render_template('index.html')
#---------קטלוג המוצרים---------
@app.route('/katalog')
def show_katalog():
    db = get_db()
    products = db.execute('''
        SELECT
            products.id,
            products.name,
            products.price,
            products.description,
            products.image_url,
            products.on_sale,
            categories.name AS category
        FROM products
        LEFT JOIN categories ON products.category_id = categories.id
    ''').fetchall()

    deals_raw = db.execute('SELECT name FROM deals').fetchall()
    deal_names = [row['name'] for row in deals_raw]  # רשימה של שמות המוצרים במבצע

    return render_template('katalog.html', products=products, deal_names=deal_names)

# הוספת מוצר חדש (GET - טופס, POST - שליחה)
@app.route('/katalog/new', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        return "גישה נדחתה – רק מנהלים יכולים להוסיף מוצרים", 403

    db = get_db()

    if request.method == 'POST':
        name        = request.form['name']
        price       = request.form['price']
        category_id = request.form['category']
        description = request.form['description']
        image_url_input = request.form.get('image_url', '').strip()
        image_file = request.files.get('image_file')
        final_image_url = save_uploaded_image(image_file) or image_url_input



        # אם הועלה קובץ תמונה תקין – נשמור אותו
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_file.save(upload_path)
            final_image_url = '/' + upload_path.replace('\\', '/')

        # אחרת אם הוזן קישור חיצוני – נשתמש בו
        elif image_url_input:
            final_image_url = image_url_input

        # הוספת המוצר
        cur = db.execute('''
            INSERT INTO products (name, price, category_id, description, image_url)
            VALUES (?, ?, ?, ?, ?)
            ''', (name, price, category_id, description, final_image_url))

        # הכנסת רשומה לטבלת המלאי עם כמות 0
        product_id = cur.lastrowid
        db.execute('INSERT INTO inventory (product_id, quantity) VALUES (?, 0)', (product_id,))

        db.commit()
        flash('המוצר נוסף בהצלחה ונרשם למלאי בכמות 0')
        return redirect(url_for('show_katalog'))

    # GET: הצגת טופס
    categories = db.execute('SELECT * FROM categories').fetchall()
    return render_template('katalog_form.html', categories=categories, product=None)



# -------------------- עריכת מוצר קיים --------------------
@app.route('/katalog/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db()

    if request.method == 'POST':
        name        = request.form['name']
        price       = request.form['price']
        category_id = request.form['category']
        description = request.form['description']
        new_image_url = request.form.get('image_url', '').strip()
        image_file     = request.files.get('image_file')

        # שליפת התמונה הקיימת
        existing = db.execute('SELECT image_url FROM products WHERE id = ?', (product_id,)).fetchone()
        final_image_url = existing['image_url'] if existing else ''


        # אם הועלה קובץ חדש – נטען אותו
        image_url_input = request.form.get('image_url', '').strip()
        image_file = request.files.get('image_file')

        if image_file and allowed_file(image_file.filename):
            final_image_url = save_uploaded_image(image_file)
        elif image_url_input:
            final_image_url = image_url_input

        # שמירת הנתונים במסד
        db.execute('''
            UPDATE products
            SET name = ?, price = ?, category_id = ?, description = ?, image_url = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
        ''', (
            name,
            price,
            category_id,
            description,
            final_image_url,
            product_id
        ))
        db.commit()
        return redirect(url_for('show_katalog'))

    # GET – הצגת טופס עם נתוני המוצר
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    categories = db.execute('SELECT * FROM categories').fetchall()
    return render_template('katalog_form.html', product=product, categories=categories)


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
    SELECT inventory.id, products.name AS product_name,
           inventory.quantity, inventory.min_required,
           inventory.updated_at
    FROM inventory
    JOIN products ON inventory.product_id = products.id''').fetchall()
    return render_template('inventory.html', inventory=inventory)

# עדכון כמות מוצר במלאי (POST)
@app.route('/inventory/update/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return "גישה נדחתה", 403

    try:
        new_quantity = int(request.form['quantity'])
        if new_quantity < 0:
            flash('⚠️ לא ניתן להזין כמות שלילית במלאי', 'error')
            return redirect(url_for('show_inventory'))
    except ValueError:
        flash('⚠️ יש להזין מספר חוקי בלבד', 'error')
        return redirect(url_for('show_inventory'))

    db = get_db()
    db.execute('''UPDATE inventory SET quantity = ?, updated_at = datetime('now', 'localtime') WHERE id = ?''', (new_quantity, item_id))
    db.commit()
    flash('✅ המלאי עודכן בהצלחה', 'success')
    return redirect(url_for('show_inventory'))


    new_quantity = request.form['quantity']
    db = get_db()
    db.execute('''UPDATE inventory SET quantity = ?, updated_at = datetime('now', 'localtime') WHERE id = ?''', (new_quantity, item_id))
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

# תבניות ולידציה
EMAIL_REGEX = r'^[^@]+@[^@]+\.[^@]+$'
PHONE_REGEX = r'^0[2-9]\d{7,8}$'
PASSWORD_REGEX = r'^(?=.*[a-zA-Z])(?=.*\d).{6,}$'
NAME_REGEX = r'^[א-תa-zA-Z\s]{2,}$'

# הרשמה של לקוח חדש
@app.route('/client/register', methods=['GET', 'POST'])
def client_register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        # בדיקות תקינות (ולידציה צד שרת)
        if not re.match(NAME_REGEX, name):
            flash("יש להזין שם תקין (לפחות 2 תווים באותיות בלבד)")
        elif not re.match(EMAIL_REGEX, email):
            flash("כתובת האימייל אינה תקינה")
        elif not re.match(PHONE_REGEX, phone):
            flash("מספר טלפון אינו תקין (לדוגמה: 0521234567)")
        elif not re.match(PASSWORD_REGEX, password):
            flash("הסיסמה צריכה להכיל לפחות 6 תווים, כולל אותיות ומספרים")
        else:
            db = get_db()
            try:
                # הוספת לקוח
                db.execute('INSERT INTO clients (name, email, phone, password) VALUES (?, ?, ?, ?)',
                           (name, email, phone, password))

                # הוספה גם לטבלת users כמשתמש רגיל (client)
                db.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
                           (email, password, 'client'))

                db.commit()
                flash('ההרשמה בוצעה בהצלחה, אנא התחבר')
                return redirect(url_for('client_login'))
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
            flash('התחברת בהצלחה!', 'success')  # ✅ כאן העדכון
            return redirect(url_for('client_profile'))
        else:
            flash('אימייל או סיסמה שגויים', 'error')

    return render_template('client_login.html')

@app.route('/client/logout')
def client_logout():
    session.pop('client_id', None)
    session.pop('client_name', None)
    flash('התנתקת בהצלחה')
    return redirect(url_for('home'))

@app.route('/logout')#התנתקות
def logout():
    session.clear()
    return redirect(url_for('home'))

#---------מבצעים---------
@app.route('/deals') #הצגת מבצעים
def show_deals():
    db = get_db()
    cursor = db.execute("SELECT id, name, image_url, original_price, discounted_price, description, updated_at FROM deals")
    deals = [dict(row) for row in cursor.fetchall()]
    return render_template('deals.html', deals=deals)

# הוספת מבצע חדש (GET - טופס, POST - שליחה)
@app.route('/add_deal', methods=['GET', 'POST'])
def add_deal():
    if not session.get('user_id') or session.get('role') != 'admin':
        flash("רק מנהלים יכולים להוסיף מבצעים.")
        return redirect(url_for('show_deals'))

    if request.method == 'POST':
        name             = request.form['name']
        image_url_input = request.form.get('image_url', '').strip()
        image_file = request.files.get('image_file')
        final_image_url = save_uploaded_image(image_file) or image_url_input
        original_price   = float(request.form['original_price'])
        discounted_price = float(request.form['discounted_price'])
        description      = request.form['description']


        # אם הועלה קובץ – שומרים בתיקייה static/images/
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            save_dir = os.path.join('static', 'images')
            os.makedirs(save_dir, exist_ok=True)

            save_path = os.path.join(save_dir, filename)
            image_file.save(save_path)

            final_image_url = '/static/images/' + filename

        # אם לא הועלה קובץ אבל הוזן קישור
        elif image_url_input:
            final_image_url = image_url_input

        print("נשמר image_url:", final_image_url)  # debug

        db = get_db()
        db.execute('''INSERT INTO deals (name, image_url, original_price, discounted_price, description, updated_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
''', (name, final_image_url, original_price, discounted_price, description))
        db.commit()

        flash("מבצע נוסף בהצלחה!")
        return redirect(url_for('show_deals'))

    return render_template('add_deal.html')

@app.route('/ai_assistant', methods=['GET', 'POST'])
def ai_assistant():
    response = ""

    if request.method == 'POST':
        question = request.form.get('question', '')
        try:
            response = run_ai_assistant(question)
        except Exception as e:
            response = f"שגיאה: {str(e)}"

    return render_template('ai_assistant.html', response=response)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
