import os
from functools import wraps

from flask import Flask, render_template, session, redirect, request, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from sqlalchemy import text, or_, func

# Creating and initializing the flask app and the database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///askanubhav.db'
db = SQLAlchemy(app)


# Faculty credentials dictionary
FACULTY_CREDENTIALS = {
    "faculty1@gmail.com": "password123",
    "faculty2@gmail.com": "pass456"
}


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

    answers = db.relationship('Answer', backref='question_reference', lazy=True)
    approval = db.relationship('QuestionApproval', uselist=False, back_populates='question')

    def __repr__(self):
        return f'<Question {self.body[:30]}>'


# Answer table with the details
class Answer(db.Model):
    __tablename__ = 'answer'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    student_id = db.Column(db.Integer, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

    question = db.relationship('Question', backref='answer_reference', lazy=True)
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

def is_faculty_email(email):
    """Check if email belongs to faculty"""
    return email.endswith('mes.ac.in') and not email.startswith('student.')

def is_student_email(email):
    """Check if email belongs to student"""
    return email.endswith('student.mes.ac.in')


# Student decorator
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 's_id' not in session:  # Check if student is logged in
            flash("Please log in as a student to access this page.", "warning")
            return redirect(url_for('login'))  # Redirect to login page
        return f(*args, **kwargs)  # If logged in, proceed with the route
    return decorated_function


# Faculty decorator
def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'faculty_email' not in session:  # Check if faculty is logged in
            flash("Please log in as a faculty member to access this page.", "warning")
            return redirect(url_for('faculty_login'))  # Redirect to faculty login page
        return f(*args, **kwargs)  # If logged in, proceed with the route
    return decorated_function


# Route for registration
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
    
    return render_template('ASK_Anubhav/Student/register.html')


@app.route('/leaderboard', methods=['GET', 'POST'])
def leaderboard():
    sort_option = request.form.get('sort', 'overall')  # Default to 'overall'

    # Base query to calculate total likes per user from the post table
    query = text("""
        SELECT u.student_id, u.username, COALESCE(SUM(p.like_count), 0) AS total_likes
        FROM user u
        LEFT JOIN post p ON u.student_id = p.student_id
    """)

    # Apply filter if 'monthly' is selected
    if sort_option == 'monthly':
        query = text("""
            SELECT u.student_id, u.username, COALESCE(SUM(p.like_count), 0) AS total_likes
            FROM user u
            LEFT JOIN post p ON u.student_id = p.student_id 
            WHERE strftime('%Y-%m', p.date_of_post) = strftime('%Y-%m', 'now')
        """)

    query = text(query.text + " GROUP BY u.student_id ORDER BY total_likes DESC")

    # Execute query
    result = db.session.execute(query).fetchall()

    # Format leaderboard data
    leaderboard_data = [
        {'rank': idx + 1, 'user': row.username, 'likes': row.total_likes}
        for idx, row in enumerate(result)
    ]

    return render_template('ASK_Anubhav/Student/leaderboard.html', leaderboard_data=leaderboard_data, sort_option=sort_option)

# Route for login
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
    
    return render_template('ASK_Anubhav/Student/login.html')


# Route for faculty login
@app.route("/faculty/login", methods=["GET", "POST"])
def faculty_login():
    if request.method == "POST":
        try:
            email = request.form.get("email")
            password = request.form.get("password")

            if email in FACULTY_CREDENTIALS and FACULTY_CREDENTIALS[email] == password:
                session['faculty_email'] = email
                return redirect(url_for("faculty_dashboard"))
            else:
                error = "Invalid email or password."
                return render_template("ASK_Anubhav/Faculty/faculty_login.html", error=error)

        except Exception as e:
            error = f"An error occurred: {str(e)}"
            print(error)
            return render_template("ASK_Anubhav/Faculty/faculty_login.html", error=error)

    return render_template("ASK_Anubhav/Faculty/faculty_login.html", error="")


# Route for faculty dashboard
@app.route("/faculty/dashboard")
@faculty_required
def faculty_dashboard():
    try:
        if 'faculty_email' not in session:
            return redirect(url_for("faculty_login"))
        return render_template("ASK_Anubhav/Faculty/faculty_dashboard.html")
    except Exception as e:
        # Handling any unexpected errors
        error = f"An error occurred: {str(e)}"
        print(error)
        return render_template("ASK_Anubhav/Faculty/faculty_dashboard.html")

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


# Route for logging out
@app.route('/logout')
@student_required
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
@app.route('/index')
@student_required
def index():
    try:
        if 's_id' not in session:
            flash("Please login to access the dashboard", "warning")
            return redirect(url_for('login'))

        page = request.args.get('page', 1, type=int)
        per_page = 5

        search_query = request.args.get('search', '').strip()

        # Start with the base query
        query = Post.query.order_by(Post.date_of_post.desc())

        # Apply search filter if there's a search query
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    func.lower(Post.title).like(func.lower(search_pattern)),
                    func.lower(Post.body).like(func.lower(search_pattern))
                )
            )

        # Apply pagination after filtering
        posts = query.paginate(page=page, per_page=per_page, error_out=False)

        username = session.get('username')

        return render_template('ASK_Anubhav/Student/index.html',
                               username=username,
                               posts=posts.items,
                               pagination=posts)

    except Exception as e:
        print(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('login'))


# Route for creating posts
@app.route('/create_post', methods=['GET', 'POST'])
@student_required
def create_post():
    try:
        if 's_id' not in session:
            flash("Please log in to create a post", "warning")
            return redirect(url_for('login'))

        username = session.get('username')

        if request.method == 'POST':
            title = request.form.get('title')
            body = request.form.get('body')
            keywords = request.form.get('keywords')
            student_id = session['s_id']

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


# Route of post page to show individual post
@app.route('/post/<int:post_id>')
@student_required
def post_details(post_id):
    try:
        if 's_id' not in session:
            flash("Please log in to create a post", "warning")
            return redirect(url_for('login'))

        post = Post.query.get_or_404(post_id)

        author = User.query.get(post.student_id)
        posted_by = author.username if author else None

        username = session.get('username')
        user_liked = session.get('user_liked', False)

        keyword_list = post.keywords.split(",") if post.keywords else []  # Splitting by commas
        keywords = [keyword.strip() for keyword in keyword_list if keyword.strip()]  # Removing spaces & empty entries
        post.keywords = keywords

        return render_template('ASK_Anubhav/Student/post_details.html', post=post, username=username, user_liked=user_liked, posted_by=posted_by)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        print(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))


# Route to like a post
@app.route('/like/<int:post_id>', methods=['POST'])
@student_required
def like_post(post_id):
    try:
        if 's_id' not in session:
            flash("Please log in to create a post", "warning")
            return redirect(url_for('login'))

        student_id = session.get('s_id')
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
        if 's_id' not in session:
            flash("Please log in to view your posts.", "warning")
            return redirect(url_for('login'))

        student_id = session['s_id']  # Assuming you store user_id in session
        my_posts = Post.query.filter_by(student_id=student_id).all()  # Fetch posts
        total_posts = len(my_posts)

        return render_template('ASK_Anubhav/Student/my_posts.html', posts=my_posts, total_posts=total_posts, username=session['username'])

    except Exception as e:
        flash(f"An error occurred while fetching your posts: {str(e)}", "danger")
        print("An error occurred while fetching your posts")
        return redirect(url_for('index'))  # Redirect to index or another appropriate page


# Route to add questions
@app.route("/questions", methods=["POST"])
@student_required
def add_question():
    try:
        if 's_id' not in session:
            flash("Please log in first", "warning")
            return redirect(url_for('login'))

        data = request.form
        title = data.get("title")
        body = data.get("detail")
        student_id = session['s_id']
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


# Route to like questions
@app.route("/questions/<int:question_id>/like", methods=["POST"])
@student_required
def like_question(question_id):
    try:
        if 's_id' not in session:
            flash("Please log in first", "warning")
            return redirect(url_for('login'))

        question = Question.query.get_or_404(question_id)
        question.like_count += 1
        db.session.commit()

        flash(f"Liked!", "success")
        return redirect(url_for('', question_id=question_id))

    except Exception as e:
        flash("An error occurred", "danger")
        print(f"An error occurred while liking the question: {str(e)}")
        return redirect(url_for('post_details', question_id=question_id))


'''
@app.route("/questions")
def questions():
    conn = get_db_connection()
    questions = conn.execute("SELECT rowid, * FROM question").fetchall()
    conn.close()
    return render_template("questions.html", questions=questions)


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")

@app.route("/api/questions/<int:question_id>/answers", methods=["GET"])
def get_answers(question_id):
    conn = get_db_connection()
    answers = conn.execute("SELECT * FROM answer WHERE question_id = ?", (question_id,)).fetchall()
    conn.close()
    return jsonify([dict(ans) for ans in answers])
    
@app.route("/api/questions/<int:question_id>/answers", methods=["POST"])
def add_answer(question_id):
    data = request.get_json()
    user_id = data.get("user_id")
    ans = data.get("ans")
    if not user_id or not ans:
        return jsonify({"success": False, "error": "User ID and answer are required"}), 400
    conn = get_db_connection()
    conn.execute("INSERT INTO answer (question_id, user_id, ans) VALUES (?, ?, ?)", (question_id, user_id, ans))
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 201

'''


# Initialize database
with app.app_context():
    try:
        db.create_all()
        print("Database created successfully")
    except Exception as e:
        print(f"Error creating database: {e}")


if __name__ == '__main__':
    app.run(debug=True)
