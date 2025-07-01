import os
from flask import Flask
from db import get_db, close_db  # ✅ שימוש בפונקציות שהועברו ל-db.py
from init_db import init_db     # ✅ שמרנו את אתחול מסד הנתונים בקובץ נפרד

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['DATABASE'] = 'database/people.db'  # ✅ הועבר ל-config

# --- הגדרות תיקיית תמונות ---
app.config['IMAGE_FOLDER'] = 'server/static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'avif'}


# --- סגירת חיבור למסד הנתונים ---
@app.teardown_appcontext
def close_connection(exception):
    close_db()

# --- רישום Blueprints ---
from routes.home_routes import home_bp
from routes.product_routes import product_bp
from routes.inventory_routes import inventory_bp
from routes.client_routes import client_bp
from routes.user_routes import user_bp
from routes.deal_routes import deal_bp
from routes.email_routes import email_bp
from routes.ai_routes import ai_bp

app.register_blueprint(home_bp)
app.register_blueprint(product_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(client_bp, url_prefix='/client')
app.register_blueprint(user_bp)
app.register_blueprint(deal_bp)
app.register_blueprint(email_bp)
app.register_blueprint(ai_bp)

# --- יצירת תיקיות דרושות ---
if not os.path.exists('database'):
    os.makedirs('database')
if not os.path.exists(app.config['IMAGE_FOLDER']):
    os.makedirs(app.config['IMAGE_FOLDER'])

# --- הרצת האפליקציה ---
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
