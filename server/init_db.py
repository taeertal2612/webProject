from db import get_db

def init_db():
    db = get_db()

    # יצירת טבלת קטגוריות
    db.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

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

    # סנכרון עם מוצרים קיימים
    product_ids = db.execute('SELECT id FROM products').fetchall()
    for product in product_ids:
        db.execute('INSERT OR IGNORE INTO inventory (product_id, quantity) VALUES (?, ?)', (product['id'], 0))

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

    db.execute('''
        INSERT OR IGNORE INTO users (id, username, password, role)
        VALUES (?, ?, ?, ?)
    ''', (1, 'manager', '1234', 'admin'))

    # טבלת מבצעים
    db.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_url TEXT,
            original_price REAL,
            discounted_price REAL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    db.execute('DELETE FROM deals')

    db.executemany('''
        INSERT OR IGNORE INTO deals (id, name, image_url, original_price, discounted_price, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'סטייק אנטריקוט', '/static/images/אנטריקוט אנגוס קפוא.avif', 89.00, 75.00, 'בשר בקר מובחר במחיר חגיגי לחברי מועדון!'),
        (2, 'חזה עוף טרי', '/static/images/חזה עוף שלם טרי.avif', 34.90, 25.00, 'חזה עוף טרי ואיכותי – רק לחברי המועדון.'),
        (3, 'קבב בקר מתובל', '/static/images/קבב בקר.avif', 89.90, 69.90, 'קבב בקר מתובל בעבודת יד – מבצע השבוע!')
    ])

    db.commit()
