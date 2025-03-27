# DON'T CHANGE THE VARIABLES THAT IVE ALREADY CREATED, IF YOU ARE PLEASE CHECK WITH THE OTHER PAGES TOO !!!

import os
from functools import wraps

from flask import Flask, render_template, session, redirect, request, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from sqlalchemy import text, or_, func
# from merged import db 


# Creating and initializing the flask app and the database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///askanubhav.db'
db = SQLAlchemy(app)


# # Faculty credentials dictionary
# FACULTY_CREDENTIALS = {
#     "faculty1@gmail.com": "password123",
#     "faculty2@gmail.com": "pass456"
# }


# Database Models
post_tags = db.Table('post_tags',
                     db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
                     db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
                     )


# Simple login for simulation with the details
class User(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    is_faculty = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return f'<User {self.username}>'


# Post table with the details
class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.String(255))
    date_of_post = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    student_id = db.Column(db.Integer, nullable=False)
    like_count = db.Column(db.Integer, default=0)

    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery', backref=db.backref('posts', lazy=True))
    approval = db.relationship('PostApproval', uselist=False, back_populates='post')


    def __repr__(self):
        return f'<Post {self.title}>'


# Question table with the details
class Question(db.Model):
    __tablename__ = 'question'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    student_id = db.Column(db.Integer, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref=db.backref('questions', lazy=True))

    approval = db.relationship('QuestionApproval', uselist=False, back_populates='question')
    answers = db.relationship('Answer', backref='question', lazy=True)


    def __repr__(self):
        return f'<Question {self.body[:30]}>'


# Answer table with the details
class Answer(db.Model):
    __tablename__ = 'answer'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    # Change this line to reference the User table instead of a non-existent student table
    student_id = db.Column(db.Integer, db.ForeignKey('user.student_id'), nullable=False)
    student = db.relationship('User', backref=db.backref('answers', lazy=True))
    
    like_count = db.Column(db.Integer, default=0)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

    approval = db.relationship('AnswerApproval', uselist=False, back_populates='answer')

    def __repr__(self):
        return f'<Answer {self.body[:30]}>'


# Tag table with tags
class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'


# Liked post table with the details
class LikePost(db.Model):
    __tablename__ = 'like_post'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    like_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LikePost PostID={self.post_id}, StudentID={self.student_id}>'


# Liked question table with the details
class LikeQuestion(db.Model):
    __tablename__ = 'like_question'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    like_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LikeQuestion QuestionID={self.question_id}, StudentID={self.student_id}>'


# Liked answer table with the details
class LikeAnswer(db.Model):
    __tablename__ = 'like_answer'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    like_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LikeAnswer AnswerID={self.answer_id}, StudentID={self.student_id}>'


# Post approval table with the details
class PostApproval(db.Model):
    __tablename__ = 'post_approval'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    remark = db.Column(db.Text)
    approver_id = db.Column(db.Integer, nullable=True)  # ID of the faculty who approved/rejected
    approval_date = db.Column(db.DateTime, default=datetime.utcnow)

    post = db.relationship('Post', back_populates='approval')

    def __repr__(self):
        return f'<PostApproval PostID={self.post_id}, Status={self.status}>'


# Question approval table with the details
class QuestionApproval(db.Model):
    __tablename__ = 'question_approval'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    remark = db.Column(db.Text)
    approver_id = db.Column(db.Integer, nullable=True)  # ID of the faculty who approved/rejected
    approval_date = db.Column(db.DateTime, default=datetime.utcnow)

    question = db.relationship('Question', back_populates='approval')

    def __repr__(self):
        return f'<QuestionApproval QuestionID={self.question_id}, Status={self.status}>'


# Answer approval table with the details
class AnswerApproval(db.Model):
    __tablename__ = 'answer_approval'
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    remark = db.Column(db.Text)
    approver_id = db.Column(db.Integer, nullable=True)  # ID of the faculty who approved/rejected
    approval_date = db.Column(db.DateTime, default=datetime.utcnow)

    answer = db.relationship('Answer', back_populates='approval')

    def __repr__(self):
        return f'<AnswerApproval AnswerID={self.answer_id}, Status={self.status}>'


# Reset database
def reset_database():
    try:
        db_file = 'askanubhav.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Deleted existing database: {db_file}")
    except Exception as e:
        print(f"Error deleting database: {e}")


# Creates and sends the session details
@app.context_processor
def inject_session():
    try:
        return dict(session=session)  # Inject session into all templates
    except Exception as e:
        print("Session not created due to: {str(e)}")
        return dict(session={})

def get_user_role(email):
    """Determine role based on email domain."""
    return "student" if email.endswith("student.mes.ac.in") else "faculty"



@app.template_filter('datetime')
def format_datetime(value):
    if not value:
        return ""
    # If value is a string, try to convert it to a datetime object
    if isinstance(value, str):
        try:
            # Handle ISO format
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except Exception:
            try:
                # Try other common date formats
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except Exception:
                # If all conversions fail, return the original string
                return value
    return value.strftime('%b %d, %Y')



def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('is_faculty') != 0:
            flash("Access restricted to students only!", "danger")
            return redirect(url_for('index'))  # Redirect to homepage
        return f(*args, **kwargs)
    return decorated_function


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Check if username or email already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already exists')
            return redirect(url_for('register'))
        
        # Determine if faculty or student based on email domain
        is_faculty = not email.endswith('student.mes.ac.in')
        
        # Create new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, is_faculty=is_faculty, email=email)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}')
            return redirect(url_for('register'))
    
    return render_template('ASK_Anubhav/Student/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['is_faculty'] = user.is_faculty
            session['student_id'] = user.student_id
            flash('Logged in successfully!')
            return redirect(url_for('index'))  # This will redirect to the index route
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    
    return render_template('ASK_Anubhav/Student/login.html')  # Corrected template path

@app.route('/index')
@app.route('/')
def index():
    try:
        if 'student_id' not in session:
            flash("Please login to access the dashboard", "warning")
            return redirect(url_for('login'))

        page = request.args.get('page', 1, type=int)
        per_page = 5
        search_query = request.args.get('search', '').strip()
        posts_query = Post.query.outerjoin(PostApproval, Post.id == PostApproval.post_id)

        if search_query:
            search_pattern = f"%{search_query}%"
            query = posts_query.filter(
                or_(func.lower(Post.title).like(func.lower(search_pattern)),
                    func.lower(Post.body).like(func.lower(search_pattern)),
                    func.lower(Post.keywords).like(func.lower(search_pattern))
                    )
                )

        if not session.get('is_faculty'):
            posts_query = posts_query.filter(or_(PostApproval.status == "Approved"))

        # Order by newest first
        posts_query = posts_query.order_by(Post.date_of_post.desc())

        pagination = posts_query.paginate(page=page, per_page=per_page, error_out=False)
        posts = pagination.items
    
        return render_template(
            'ASK_Anubhav/Student/index.html',
            posts=posts,
            pagination=pagination,
            total_posts=posts_query.count(),
            search_query=search_query,
            username=session.get('username', 'Guest')
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        flash("Something went wrong!", "danger")
        return redirect(url_for('login'))


# @app.route('/logout')
# def logout():
#     session.pop('username', None)
#     session.pop('is_faculty', None)
#     session.pop('student_id', None)
#     flash('Logged out successfully!')
#     return redirect(url_for('login'))

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         try:
#             username = request.form.get('username')
#             email = request.form.get('email')
#             password = request.form.get('password')

       
#             if User.query.filter_by(email=email).first():
#                 flash('Email already registered', 'danger')
#                 return redirect(url_for('register'))

#             if User.query.filter_by(username=username).first():
#                 flash('Username already taken', 'danger')
#                 return redirect(url_for('register'))

#             if not email.endswith(('mes.ac.in', 'student.mes.ac.in')):
#                 flash('Please use institutional email (@mes.ac.in or @student.mes.ac.in)', 'warning')
#                 return redirect(url_for('register'))

#         except Exception as e:
#             flash("An error occurred", "danger")
#             print(f"An error occurred: {str(e)}")
            

        
#         new_user = User(username=username, email=email, password=password, role=get_user_role(email))
#         db.session.add(new_user)
#         db.session.commit()

#         flash('Registration successful! Please login.', 'success')
#         return redirect(url_for('login'))

#     return render_template('ASK_Anubhav/Student/register.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form.get('email')
#         password = request.form.get('password')

#         user = User.query.filter_by(email=email).first()

#         if not user or user.password != password:  
#             flash('Invalid email or password', 'danger')
#             return redirect(url_for('login'))

#         # Set session
#         session['user_id'] = user.id
#         session['username'] = user.username
#         session['is_role'] = user.role  
#         session['email'] = user.email

#         flash(f'Welcome back, {user.username}!', 'success')

#         return redirect(url_for('faculty_posts' if user.role == "faculty" else 'index'))

#     return render_template('ASK_Anubhav/Student/login.html')




# Route for login
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         try:
#             username = request.form.get('username')
#             password = request.form.get('password')

#             user = User.query.filter_by(username=username).first()
#             if not user or not check_password_hash(user.password, password):
#                 flash('Invalid details')
#                 return redirect(url_for('login'))

#             session['student_id'] = user.student_id
#             session['username'] = user.username
#             flash("Login successful", "success")
#             return redirect(url_for('index'))

#         except Exception as e:
#             print(f"An error occurred: {str(e)}")
#             return redirect(url_for('login'))

@app.route('/approve_post/<int:post_id>', methods=['POST'])
def approve_post(post_id):
    if 'username' not in session or not session.get('is_faculty'):
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('index'))

    try:
        post = Post.query.get(post_id)
        if not post:
            flash('Post not found!', 'danger')
            return redirect(url_for('index'))
        
        # Check if there's an existing approval record
        approval = PostApproval.query.filter_by(post_id=post_id).first()
        
        if approval:
            # Update existing approval
            approval.status = "Approved"
            approval.remark = None
            approval.approver_id = session.get('student_id')
            approval.approval_date = datetime.now()
        else:
            # Create new approval record
            approval = PostApproval(
                post_id=post_id,
                status="Approved",
                remark=None,
                approver_id=session.get('student_id'),
                approval_date=datetime.now()
            )
            db.session.add(approval)  
        
        db.session.commit()

        flash('Post approved successfully!', 'success')

    except Exception as e:
        db.session.rollback() 
        flash(f'Error: {str(e)}', 'danger')

    finally:
        db.session.close()  
    return redirect(url_for('index'))

# Route to reject a post
@app.route('/reject_post/<int:post_id>', methods=['POST'])
def reject_post(post_id):
    if 'username' not in session or not session.get('is_faculty'):
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('index'))

    try:
        post = Post.query.get(post_id)
        if not post:
            flash('Post not found!', 'danger')
            return redirect(url_for('index'))

        # Get the rejection remark from the form
        remark = request.form.get('remark', '')
        
        # Check if there's an existing approval record
        approval = PostApproval.query.filter_by(post_id=post_id).first()
        
        if approval:
            # Update existing approval
            approval.status = "Rejected"
            approval.remark = remark
            approval.approver_id = session.get('student_id')
            approval.approval_date = datetime.now()
        else:
            # Create new approval record
            approval = PostApproval(
                post_id=post_id,
                status="Rejected",
                remark=remark,
                approver_id=session.get('student_id'),
                approval_date=datetime.now()
            )
            db.session.add(approval)  
        
        db.session.commit()  

        flash('Post rejected successfully!', 'success')

    except Exception as e:
        db.session.rollback() 
        flash(f'Error: {str(e)}', 'danger')

    finally:
        db.session.close() 
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    try:
        session.clear()
        flash("You have been logged out", "info")
        return redirect(url_for('login'))
    except Exception as e:
        # Handling any unexpected errors
        print(f"An error occurred during logout: {str(e)}", "danger")
        return redirect(url_for('login'))


# Route for student home page where the posts are shown
# @app.route('/index')
# @student_required
# def index():
#     try:
#         if 'student_id' not in session:
#             flash("Please login to access the dashboard", "warning")
#             return redirect(url_for('login'))

#         page = request.args.get('page', 1, type=int)
#         per_page = 5

#         search_query = request.args.get('search', '').strip()

#         # Start with the base query
#         query = Post.query.order_by(Post.date_of_post.desc())

#         # Apply search filter if there's a search query
#         if search_query:
#             search_pattern = f"%{search_query}%"
#             query = query.filter(
#                 or_(
#                     func.lower(Post.title).like(func.lower(search_pattern)),
#                     func.lower(Post.body).like(func.lower(search_pattern))
#                 )
#             )

#         # Apply pagination after filtering
#         posts = query.paginate(page=page, per_page=per_page, error_out=False)

#         username = session.get('username')

#         return render_template('ASK_Anubhav/Student/index.html',
#                                username=username,
#                                posts=posts.items,
#                                pagination=posts)

#     except Exception as e:
#         print(f"An error occurred: {str(e)}", "danger")
#         return redirect(url_for('login'))


# Route for creating posts
@app.route('/create_post', methods=['GET', 'POST'])
# @student_required
def create_post():
    try:
        if 'student_id' not in session:
            flash("Please log in to create a post", "warning")
            return redirect(url_for('login'))

        username = session.get('username')

        if request.method == 'POST':
            title = request.form.get('title')
            body = request.form.get('body')
            keywords = request.form.get('keywords')
            student_id = session['student_id']

            new_post = Post(title=title, body=body, keywords=keywords, student_id=student_id)
            db.session.add(new_post)
            db.session.commit()

            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]

            for keyword in keyword_list:
                # Check if the tag already exists
                tag = Tag.query.filter_by(name=keyword).first()
                if not tag:
                    tag = Tag(name=keyword)
                    db.session.add(tag)

                # Associate tag with the post
                new_post.tags.append(tag)

            db.session.commit()

            flash("Post created successfully", "success")
            return redirect(url_for('index'))

        return render_template('ASK_Anubhav/Student/create_post.html', username=username)

    except Exception as e:
        flash("An error occurred", "danger")
        print(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))
    
@app.route('/ask_question', methods=['GET', 'POST'])
def ask_question():
    try:
        if 'student_id' not in session:
            flash("Please log in to ask a question", "warning")
            return redirect(url_for('login'))

        username = session.get('username')

        if request.method == 'POST':
            title = request.form.get('title')
            body = request.form.get('body')
            post_id = request.form.get('post_id')  # Post ID to which the question belongs
            student_id = session['student_id']

            # Insert the question into the database
            new_question = Question(
                title=title,
                body=body,
                student_id=student_id,
                like_count=0,
                post_id=post_id
            )
            db.session.add(new_question)
            db.session.commit()

            flash("Question asked successfully", "success")
            return redirect(url_for('index'))

        return render_template('ASK_Anubhav/Student/ask_question.html', username=username)

    except Exception as e:
        flash("An error occurred", "danger")
        print(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))
    
@app.route('/my_questions')
def my_questions():
    if 'student_id' not in session:  # Ensure student is logged in
        return redirect(url_for('login'))

    student_id = session['student_id']  # Fetch student_id from session
    questions = Question.query.filter_by(student_id=student_id).all()

    return render_template('ASK_Anubhav/Student/my_questions.html', questions=questions, total_questions=len(questions))

@app.route('/question/<int:question_id>')
def question_details(question_id):
    question = Question.query.get_or_404(question_id)
    return render_template('question_detail.html', question=question, username=session.get('username'))


@app.route('/post/<int:post_id>')
def post_details(post_id):
    try:
        if 'student_id' not in session:
            flash("Please log in to view the post", "warning")
            return redirect(url_for('login'))

        post = Post.query.get_or_404(post_id)
        author = User.query.get(post.student_id)
        posted_by = author.username if author else None

        username = session.get('username')
        student_id = session.get('student_id')
        user_liked = LikePost.query.filter_by(student_id=student_id, post_id=post_id).first()

        print("Final post.keywords:", type(post.keywords), post.keywords)

        keyword_list = post.keywords.split(",") if post.keywords else []  # Splitting by commas
        keywords = [keyword.strip() for keyword in keyword_list if keyword.strip()]  # Removing spaces & empty entries
        # post.keywords = keywords

        # **Add Questions Related to This Post**
        questions = Question.query.filter_by(post_id=post_id).all()  # Fetch only matching post_id

        return render_template('ASK_Anubhav/Student/post_details.html', post=post, username=username, user_liked=user_liked, posted_by=posted_by, questions=questions, keywords=keyword_list, student_id=student_id)  # **Pass questions to template**
    
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        print(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))

@app.route('/add_question_2', methods=['POST'])
def add_question_2():
    try:
        data = request.get_json()
        title = data.get("title")
        body = data.get("body")
        post_id = data.get("post_id")

        if not title or not body:
            return jsonify({"status": "error", "message": "Title and body are required"}), 400

        # Assuming session["student_id"] holds the logged-in user's ID
        student_id = session.get("student_id")
        if not student_id:
            return jsonify({"status": "error", "message": "User not logged in"}), 401

        # Create and save the question
        new_question = Question(title=title, body=body, post_id=post_id, student_id=student_id, like_count=0)
        db.session.add(new_question)
        db.session.commit()

        # Return success response with question data including the ID
        return jsonify({
            "status": "success",
            "message": "Question added successfully",
            "question": {
                "id": new_question.id,  # Include this ID for the data-question-id attribute
                "title": new_question.title,
                "body": new_question.body,
                "like_count": new_question.like_count
            }
        }), 200

    except Exception as e:
        print(f"Error adding question: {str(e)}")  # Logs error in terminal
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/answer_2', methods=['POST'])
def add_answer():
    if 'student_id' not in session:
        return jsonify({"status": "error", "message": "Login required"}), 403

    data = request.get_json()
    answer_body = data.get('body')
    question_id = data.get('question_id')

    if not answer_body or not question_id:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    new_answer = Answer(body=answer_body, student_id=session['student_id'], question_id=question_id, like_count=0)
    db.session.add(new_answer)
    db.session.commit()

    # This looks good, but could also return the answer details for more flexibility
    return jsonify({"status": "success", "answer_id": new_answer.id})

@app.route('/like_question_2', methods=['POST'])
def like_question_2():
    if 'student_id' not in session:
        return jsonify({"status": "error", "message": "Login required"}), 403

    data = request.get_json()
    question_id = data.get('question_id')
    student_id = session['student_id']

    # Check if user already liked this question
    existing_like = LikeQuestion.query.filter_by(student_id=student_id, question_id=question_id).first()
    
    if existing_like:
        # If already liked, unlike it (toggle behavior)
        db.session.delete(existing_like)
        db.session.commit()
        action = "unliked"
    else:
        # If not liked, add a like
        new_like = LikeQuestion(student_id=student_id, question_id=question_id)
        db.session.add(new_like)
        db.session.commit()
        action = "liked"
    
    # Get updated like count
    like_count = LikeQuestion.query.filter_by(question_id=question_id).count()
    
    # Update the question's like_count
    question = Question.query.get(question_id)
    if question:
        question.like_count = like_count
        db.session.commit()

    return jsonify({
        "status": "success", 
        "action": action,
        "like_count": like_count
    })

@app.route('/like_answer_2', methods=['POST'])
def like_answer_2():
    if 'student_id' not in session:
        return jsonify({"status": "error", "message": "Login required"}), 403

    data = request.get_json()
    answer_id = data.get('answer_id')
    student_id = session['student_id']

    # Check if user already liked this answer
    existing_like = LikeAnswer.query.filter_by(student_id=student_id, answer_id=answer_id).first()

    if existing_like:
        # If already liked, unlike it (toggle behavior)
        db.session.delete(existing_like)
        db.session.commit()
        action = "unliked"
    else:
        # If not liked, add a like
        new_like = LikeAnswer(student_id=student_id, answer_id=answer_id)
        db.session.add(new_like)
        db.session.commit()
        action = "liked"

    # Get updated like count
    like_count = LikeAnswer.query.filter_by(answer_id=answer_id).count()
    
    # Update the answer's like_count
    answer = Answer.query.get(answer_id)
    if answer:
        answer.like_count = like_count
        db.session.commit()

    return jsonify({
        "status": "success", 
        "action": action,
        "like_count": like_count
    })

# Route to like a post
@app.route('/like/<int:post_id>', methods=['POST'])
@student_required
def like_post(post_id):
    try:
        if 'student_id' not in session:
            flash("Please log in to create a post", "warning")
            return redirect(url_for('login'))

        student_id = session.get('student_id')
        post = Post.query.get_or_404(post_id)
        user_liked = False

        session.pop('user_liked', None)

        # check if the post is already liked
        already_liked = LikePost.query.filter_by(post_id=post_id, student_id=student_id).first()
        if already_liked:
            db.session.delete(already_liked)
            post.like_count -= 1
            user_liked = False
            flash('unliked')
        else:
            like = LikePost(post_id=post_id, student_id=student_id)
            post.like_count += 1
            user_liked = True
            db.session.add(like)
            flash('liked')

        db.session.commit()
        print(f"User liked: {user_liked}")
        session['user_liked'] = user_liked
        return redirect(url_for('post_details', post_id=post_id))

    except Exception as e:
        flash("An error occurred", "danger")
        print(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))


# Route to show a user's own posts
@app.route('/my_posts')
@student_required
def my_posts():
    try:
        if 'student_id' not in session:
            flash("Please log in to view your posts.", "warning")
            return redirect(url_for('login'))

        page = request.args.get('page', 1, type=int)

        student_id = session.get('student_id')
        total_posts = Post.query.filter_by(student_id=student_id).count()

        username = session.get('username')

        # ✅ Get all posts by this student, including approval status
        posts_query = db.session.query(
            Post, PostApproval.status
        ).outerjoin(PostApproval, Post.id == PostApproval.post_id).filter(
            Post.student_id == student_id
        ).order_by(Post.date_of_post.desc())

        # ✅ Paginate results
        pagination = posts_query.paginate(page=page, per_page=5, error_out=False)
        posts = pagination.items

        return render_template(
            'ASK_Anubhav/Student/my_posts.html',
            posts=posts,
            pagination=pagination,
            student_id=student_id,
            username=username,
            total_posts=total_posts
        )

    except Exception as e:
        flash(f"An error occurred while fetching your posts: {str(e)}", "danger")
        print("An error occurred while fetching your posts")
        return redirect(url_for('index'))


# Route to add questions
@app.route("/questions", methods=["POST"])
@student_required
def add_question():
    try:
        if 'student_id' not in session:
            flash("Please log in first", "warning")
            return redirect(url_for('login'))

        data = request.form
        title = data.get("title")
        body = data.get("detail")
        student_id = session['student_id']
        post_id = data.get("post_id")

        if not title or not body or not post_id:
            flash("Title, detail, and post_id are required", "warning")
            return redirect(url_for('post_details'))  # Replace with your actual create question page

        new_question = Question(
            title=title,
            body=body,
            student_id=student_id,
            post_id=post_id
        )

        db.session.add(new_question)
        db.session.commit()

        flash("Question added successfully", "success")
        return redirect(url_for('post_details', post_id=post_id))

    except Exception as e:
        flash("An error occurred", "danger")
        print(f"An error occurred: {str(e)}")
        return redirect(url_for('post_details'))

# Import necessary modules

@app.route('/qa_forum')
def qa_forum():
    # Get all questions
    questions = db.session.query(Question).all()
    
    # For each question, load its answers
    for question in questions:
        # Get all answers for this question
        answers = db.session.query(Answer).filter(Answer.question_id == question.id).all()
        question.answers = answers
    
    return render_template('ASK_Anubhav/Student/qa_forum.html', questions=questions, username=session.get('username'))

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if session.get('is_faculty') != 0:  # Check if user is not a student
        flash("Only students can submit answers.", "danger")
        return redirect(url_for('qa_forum'))
    
    question_id = request.form.get('question_id')
    answer_body = request.form.get('answer_body')
    student_id = session.get('student_id')
    
    if not question_id or not answer_body:
        flash("Answer cannot be empty.", "danger")
        return redirect(url_for('qa_forum'))
    
    # Since we can't modify the model, we'll use raw SQL to insert the answer
    try:
        # Insert the answer
        answer = Answer(body=answer_body, student_id=student_id, question_id=question_id, like_count=0)
        db.session.add(answer)
        db.session.flush()  # This will assign an ID to the answer
        
        # Create a pending approval status
        approval = AnswerApproval(answer_id=answer.id, status='pending')
        db.session.add(approval)
        
        db.session.commit()
        flash("Answer submitted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error submitting answer: {str(e)}", "danger")
    
    return redirect(url_for('qa_forum'))

@app.route('/approve_question/<int:question_id>', methods=['POST'])
def approve_question(question_id):
    if not session.get('is_faculty'):
        flash("Unauthorized action!", "danger")
        return redirect(url_for('qa_forum'))
    
    question = Question.query.get_or_404(question_id)
    
    # Check if question already has an approval record
    if not question.approval:
        # Create a new QuestionApproval record
        approval = QuestionApproval(question_id=question_id, status='approved')
        db.session.add(approval)
    else:
        # Update existing approval status
        question.approval.status = 'approved'
    
    db.session.commit()
    flash("Question Approved!", "success")
    return '', 200

@app.route('/reject_question/<int:question_id>', methods=['POST'])
def reject_question(question_id):
    if not session.get('is_faculty'):
        flash("Unauthorized action!", "danger")
        return redirect(url_for('qa_forum'))
    
    question = Question.query.get_or_404(question_id)
    
    # Check if question already has an approval record
    if not question.approval:
        # Create a new QuestionApproval record
        approval = QuestionApproval(question_id=question_id, status='rejected')
        db.session.add(approval)
    else:
        # Update existing approval status
        question.approval.status = 'rejected'
    
    db.session.commit()
    flash("Question Rejected!", "danger")
    return '', 200

@app.route('/approve_answer/<int:answer_id>', methods=['POST'])
def approve_answer(answer_id):
    if not session.get('is_faculty'):
        flash("Unauthorized action!", "danger")
        return redirect(url_for('qa_forum'))
    
    answer = Answer.query.get_or_404(answer_id)
    
    # Check if answer already has an approval record
    if not answer.approval:
        # Create a new AnswerApproval record
        approval = AnswerApproval(answer_id=answer_id, status='approved')
        db.session.add(approval)
    else:
        # Update existing approval status
        answer.approval.status = 'approved'
    
    db.session.commit()
    flash("Answer Approved!", "success")
    return '', 200

@app.route('/reject_answer/<int:answer_id>', methods=['POST'])
def reject_answer(answer_id):
    if not session.get('is_faculty'):
        flash("Unauthorized action!", "danger")
        return redirect(url_for('qa_forum'))
    
    answer = Answer.query.get_or_404(answer_id)
    
    # Check if answer already has an approval record
    if not answer.approval:
        # Create a new AnswerApproval record
        approval = AnswerApproval(answer_id=answer_id, status='rejected')
        db.session.add(approval)
    else:
        # Update existing approval status
        answer.approval.status = 'rejected'
    
    db.session.commit()
    flash("Answer Rejected!", "danger")
    return '', 200

@app.route('/like_question/<int:question_id>', methods=['POST'])
def like_question(question_id):
    question = Question.query.get_or_404(question_id)
    question.like_count = (question.like_count or 0) + 1
    db.session.commit()
    return '', 200

@app.route('/like_answer/<int:answer_id>', methods=['POST'])
def like_answer(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    answer.like_count = (answer.like_count or 0) + 1
    db.session.commit()
    return '', 200



@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post, username=session.get('username'))

# Leaderboard route remains unchanged
@app.route('/leaderboard')
def leaderboard():
    filter_type = request.args.get('filter', 'overall')
    
    posts_query = """
        SELECT 
            'post' as content_type,
            p.id,
            p.title,
            p.like_count,
            u.username as author,
            p.date_of_post as date_created
        FROM 
            post p
        JOIN 
            user u ON p.student_id = u.student_id
    """
    
    questions_query = """
        SELECT 
            'question' as content_type,
            q.id,
            q.title,
            q.like_count,
            u.username as author,
            p.date_of_post as date_created
        FROM 
            question q
        JOIN 
            user u ON q.student_id = u.student_id
        JOIN 
            post p ON q.post_id = p.id
    """
    
    answers_query = """
        SELECT 
            'answer' as content_type,
            a.id,
            CASE
                WHEN LENGTH(a.body) > 30 THEN SUBSTR(a.body, 1, 30) || '...'
                ELSE a.body
            END as title,
            a.like_count,
            u.username as author,
            CURRENT_TIMESTAMP as date_created
        FROM 
            answer a
        JOIN 
            user u ON a.student_id = u.student_id
    """
    
    if filter_type == 'month':
        first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        posts_query += f" WHERE p.date_of_post >= '{first_day}'"
        questions_query += f" WHERE p.date_of_post >= '{first_day}'"
    
    combined_query = f"""
        {posts_query}
        UNION ALL
        {questions_query}
        UNION ALL
        {answers_query}
        ORDER BY like_count DESC
        LIMIT 30
    """
    
    results = db.session.execute(text(combined_query))
    
    leaderboard_data = []
    rank = 1
    
    for row in results:
        leaderboard_data.append({
            'rank': rank,
            'content_type': row.content_type,
            'id': row.id,
            'title': row.title if row.title else 'Untitled',
            'like_count': row.like_count or 0,
            'author': row.author,
            'date_created': row.date_created
        })
        rank += 1
    
    return render_template('ASK_Anubhav/Student/leaderboard.html', leaderboard=leaderboard_data, filter_type=filter_type, username=session.get('username'))

# Initialize database
with app.app_context():
    try:
        db.create_all()
        print("Database created successfully")
    except Exception as e:
        print(f"Error creating database: {e}")


if __name__ == '__main__':
    app.run(debug=True)
