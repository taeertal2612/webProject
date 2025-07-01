from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('home.dashboard'))
        else:
            flash('שם משתמש או סיסמה שגויים')
    return render_template('login.html')

@user_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.home'))
