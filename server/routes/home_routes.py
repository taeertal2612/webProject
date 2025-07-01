from flask import Blueprint, render_template, session, redirect, url_for

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    return render_template('index.html')

@home_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    return render_template('dashboard.html', username=session['username'], role=session['role'])
