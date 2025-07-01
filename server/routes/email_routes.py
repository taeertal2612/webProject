from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db import get_db
from send_email import send_email_to_all_clients

email_bp = Blueprint('email', __name__)

@email_bp.route('/send_email', methods=['GET', 'POST'])
def send_email_page():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('user.login'))

    db = get_db()
    success = None

    if request.method == 'POST':
        subject = request.form['subject']
        content = request.form['content']
        recipients = [row['email'] for row in db.execute('SELECT email FROM clients').fetchall()]
        send_email_to_all_clients(subject, content, recipients)
        success = f"המייל נשלח ל-{len(recipients)} לקוחות"

    return render_template('send_email.html', success=success)
