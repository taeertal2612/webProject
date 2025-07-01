from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db
import re

client_bp = Blueprint('client', __name__)

EMAIL_REGEX = r'^[^@]+@[^@]+\.[^@]+$'
PHONE_REGEX = r'^0[2-9]\d{7,8}$'
PASSWORD_REGEX = r'^(?=.*[a-zA-Z])(?=.*\d).{6,}$'
NAME_REGEX = r'^[א-תa-zA-Z\s]{2,}$'

@client_bp.route('/register', methods=['GET', 'POST'])
def client_register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        password = request.form['password'].strip()

        if not re.match(NAME_REGEX, name):
            flash("שם לא תקין")
        elif not re.match(EMAIL_REGEX, email):
            flash("אימייל לא תקין")
        elif not re.match(PHONE_REGEX, phone):
            flash("טלפון לא תקין")
        elif not re.match(PASSWORD_REGEX, password):
            flash("סיסמה לא תקינה")
        else:
            db = get_db()
            try:
                db.execute('INSERT INTO clients (name, email, phone, password) VALUES (?, ?, ?, ?)', (name, email, phone, password))
                db.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)', (email, password, 'client'))
                db.commit()
                flash("ההרשמה הצליחה!")
                return redirect(url_for('client.client_login'))
            except:
                flash("האימייל כבר קיים")

    return render_template('client_register.html')

@client_bp.route('/login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        client = db.execute('SELECT * FROM clients WHERE email=? AND password=?', (email, password)).fetchone()

        if client:
            session['client_id'] = client['id']
            session['client_name'] = client['name']
            return redirect(url_for('client.client_profile'))
        else:
            flash("אימייל או סיסמה שגויים")

    return render_template('client_login.html')

@client_bp.route('/logout')
def client_logout():
    session.pop('client_id', None)
    session.pop('client_name', None)
    flash("התנתקת בהצלחה")
    return redirect(url_for('home.home'))

@client_bp.route('/profile')
def client_profile():
    if 'client_id' not in session:
        return redirect(url_for('client.client_register'))
    db = get_db()
    client = db.execute('SELECT * FROM clients WHERE id = ?', (session['client_id'],)).fetchone()
    return render_template('client_profile.html', client=client)

@client_bp.route('/edit', methods=['GET', 'POST'])
def client_edit():
    if 'client_id' not in session:
        return redirect(url_for('client.client_login'))
    
    db = get_db()
    client = db.execute('SELECT * FROM clients WHERE id = ?', (session['client_id'],)).fetchone()

    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        password = request.form['password'].strip()

        if not re.match(NAME_REGEX, name):
            flash("שם לא תקין")
        elif not re.match(EMAIL_REGEX, email):
            flash("אימייל לא תקין")
        elif not re.match(PHONE_REGEX, phone):
            flash("טלפון לא תקין")
        else:
            db.execute('UPDATE clients SET name=?, email=?, phone=? WHERE id=?', (name, email, phone, session['client_id']))
            if password:
                if not re.match(PASSWORD_REGEX, password):
                    flash("סיסמה לא תקינה")
                else:
                    db.execute('UPDATE clients SET password=? WHERE id=?', (password, session['client_id']))
            db.commit()
            flash("הפרטים עודכנו בהצלחה")

            # עדכון session
            session['client_name'] = name

            return redirect(url_for('client.client_profile'))

    return render_template('client_edit.html', client=client)

@client_bp.route('/delete', methods=['GET', 'POST'])
def client_delete():
    if 'client_id' not in session:
        return redirect(url_for('client.client_login'))

    if request.method == 'POST':
        db = get_db()
        db.execute('DELETE FROM clients WHERE id = ?', (session['client_id'],))
        db.commit()
        session.pop('client_id', None)
        session.pop('client_name', None)
        flash("החשבון נמחק בהצלחה")
        return redirect(url_for('home.home'))

    return render_template('client_delete.html')
