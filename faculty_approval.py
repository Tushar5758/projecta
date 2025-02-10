from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey123' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///askanubhav.db'
db = SQLAlchemy(app)

# Models remain the same
class User(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_faculty = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    date_of_post = db.Column(db.DateTime, default=datetime.utcnow)
    like_count = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('user.student_id'))

class PostApproval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    status = db.Column(db.String(20))
    remark = db.Column(db.Text)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.student_id'))
    approval_date = db.Column(db.DateTime, default=datetime.utcnow)

# Utility functions for email validation
def is_faculty_email(email):
    """Check if email belongs to faculty"""
    return email.endswith('mes.ac.in') and not email.startswith('student.')

def is_student_email(email):
    """Check if email belongs to student"""
    return email.endswith('student.mes.ac.in')

# Decorators remain the same
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def faculty_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_faculty'):
            flash('Access denied. Faculty only.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Updated routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation checks
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return redirect(url_for('register'))
        
        # Email domain validation
        if not (is_faculty_email(email) or is_student_email(email)):
            flash('Please use your institutional email (@mes.ac.in or @student.mes.ac.in)')
            return redirect(url_for('register'))
        
        # Create new user with role based on email
        new_user = User(
            username=username,
            email=email,
            password=password,  # In production, use password hashing
            is_faculty=is_faculty_email(email)
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Email not registered')
            return redirect(url_for('login'))
        
        if user.password != password:  # In production, use proper password verification
            flash('Incorrect password')
            return redirect(url_for('login'))
        
        # Set session data
        session['user_id'] = user.student_id
        session['username'] = user.username
        session['is_faculty'] = user.is_faculty
        session['email'] = user.email
        
        flash(f'Welcome back, {user.username}!')
        return redirect(url_for('index'))
    
    return render_template('login.html')

# Rest of the routes remain the same
@app.route('/')
@login_required
def index():
    posts = Post.query.order_by(Post.date_of_post.desc()).all()
    return render_template('index.html', 
                         posts=posts, 
                         username=session.get('username'),
                         is_faculty=session.get('is_faculty'),
                         total_posts=len(posts))

@app.route('/approve_post/<int:post_id>')
@faculty_required
def approve_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    approval = PostApproval(
        post_id=post_id,
        status='approved',
        approver_id=session['user_id'],
        approval_date=datetime.utcnow()
    )
    
    db.session.add(approval)
    db.session.commit()
    
    flash('Post approved successfully')
    return redirect(url_for('index'))

@app.route('/reject_post/<int:post_id>')
@faculty_required
def reject_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    approval = PostApproval(
        post_id=post_id,
        status='rejected',
        approver_id=session['user_id'],
        approval_date=datetime.utcnow()
    )
    
    db.session.add(approval)
    db.session.delete(post)
    db.session.commit()
    
    flash('Post rejected and deleted')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)