import sqlite3
from flask import g, current_app

def get_db():
    """
    פותח חיבור למסד הנתונים אם טרם נפתח, ושומר אותו במשתנה גלובלי של Flask
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

def close_db(_=None):
    """
    סוגר את החיבור למסד הנתונים בסיום הבקשה
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
