from flask import Flask, render_template, request, flash, redirect, url_for, session
from app import app
from models import db, User, Subject, Quiz, Question, QuizResult, Chapter, UserAnswer
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

@app.route('/')
def home():
    return render_template('home.html')

# Route to register new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        cpassword = request.form.get('cpassword', '').strip()
        name = request.form.get('name', '').strip()
        qualification = request.form.get('qualification', '').strip()
        dob = request.form.get('dob', '').strip()

        if not all([username, password, cpassword, name, qualification, dob]):
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))
        
        if password != cpassword:
            flash('Password does not match', 'danger')
            return redirect(url_for('register'))
        
        #check user in database
        user = User.query.filter_by(username=username).first()
        if user:
            flash('User already exists!', 'danger')
            return redirect(url_for('register'))

        #hashing the password
        hash_password = generate_password_hash(password)   

        #create user
        new_user = User(username=username, password=hash_password, name=name, qualification=qualification, dob=dob)

     
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully', 'success')
        return redirect(url_for('login'))
    

    return render_template('register.html')

#login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        if not all([username, password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('User does not exist', 'danger')
            return redirect(url_for('login'))
        
        if not check_password_hash(user.password, password):
            flash('Password is incorrect', 'danger')
            return redirect(url_for('login'))
        
        session['id'] = user.id
        session['user'] = user.username
        session['name'] = user.name
        session['is_admin'] = user.is_admin

        if user.is_admin:
            flash('Admin login successfully', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login successfully', 'success')
            return redirect(url_for('user_dashboard'))
    return render_template('login.html')

# decorator for user required
def user_required(func):
    """Restrict access to user-only pages (block admins)."""
    @wraps(func)
    def inner(*args, **kwargs):
        if "id" not in session:
            flash('Please login to continue', 'info')
            return redirect(url_for('login'))
        
        user = User.query.get(session['id'])
        if not user:  
            flash('User not found, please login again', 'danger')
            return redirect(url_for('login'))

        if user.is_admin:  # Block admin access
            flash('You are not allowed to access this page', 'danger')
            return redirect(url_for('home'))  # Redirect admin to home

        return func(*args, **kwargs)

    return inner

#decorator for admin required
def admin_required(func):
    """Restrict access to admin-only pages (block normal users)."""
    @wraps(func)
    def inner(*args, **kwargs):
        if 'id' not in session:
            flash('Please login to continue', 'danger')
            return redirect(url_for('login'))

        user = User.query.get(session['id'])
        if not user:  
            flash('User not found, please login again', 'danger')
            return redirect(url_for('login'))

        if not user.is_admin:  # Block normal user access
            flash('You are not authorized to access this page', 'danger')
            return redirect(url_for('home'))  # Redirect user to home

        return func(*args, **kwargs)

    return inner 

#logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logout Successfully', 'info')
    return redirect(url_for('login'))

#admin dashboard
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    user = session.get('name', 'User')
    subjects = Subject.query.all()
    return render_template("admin_side/admin_dashboard.html", user=user, subjects=subjects)

#Admin side view Quizzes
@app.route('/admin/view_quizzes')
@admin_required
def view_quizzes():
    quizzes = Quiz.query.all()
    return render_template("admin_side/view_quizzes.html", quizzes=quizzes)

#Admin side summary
@app.route('/admin/summary')
@admin_required
def summary():
    quizzes = Quiz.query.all()

    summary_data = []
    for quiz in quizzes:
        total_users = User.query.filter_by(is_admin=False).count()  # Count non-admin users only
        attempted_users = (
            QuizResult.query
            .join(User)
            .filter(QuizResult.quiz_id == quiz.id, User.is_admin == False)
            .count()
        )
        not_attempted_users = total_users - attempted_users

        summary_data.append({
            'quiz_id': quiz.id,
            'quiz_Id': quiz.quizId,
            'title': quiz.title,
            'attempted': attempted_users,
            'not_attempted': not_attempted_users
        })

    return render_template("admin_side/summary.html", summary_data=summary_data)

#admin seach route
@app.route('/admin/search')
@admin_required
def search():
    return render_template("admin_side/search.html")

#--------------User Side Routes----------------

#User side dashboard
@app.route('/user/dashboard')
@user_required
def user_dashboard():
    user_id = session.get('id')
    user = session.get('name', 'User')
    quizzes = Quiz.query.all()

    now = datetime.now()
    # Get the list of quiz IDs that the user has attempted
    attempted_quiz = (
        db.session.query(QuizResult.quiz_id)
        .filter(QuizResult.user_id == user_id)
        .all()
    )
    attempted_quiz_id = [attempt.quiz_id for attempt in attempted_quiz]
    return render_template("user_side/user_dashboard.html", user=user, quizzes=quizzes, 
                           attempted_quiz_id=attempted_quiz_id, now=now)

#User side score route
@app.route('/user/score')
@user_required
def user_score():
    user_id = session.get('id')

    if not user_id:
        flash("You must be logged in to view results.", "danger")
        return redirect(url_for('login'))

    # Fetch all quiz attempts by the user
    attempts = (
        db.session.query(QuizResult, Quiz.title, Quiz.quizId)
        .join(Quiz, QuizResult.quiz_id == Quiz.id)
        .filter(QuizResult.user_id == user_id)
        .order_by(QuizResult.quiz_attempt_date.desc())  # Show latest attempts first
        .all()
    )
    return render_template("user_side/user_score.html", attempts=attempts)

#User side summary route
@app.route('/user/summary')
@user_required
def user_summary():
    user_id = session.get('id')

    if not user_id:
        flash("You must be logged in to view results.", "danger")
        return redirect(url_for('login'))

    # Fetch user's quiz attempts with quiz titles
    attempts = (
        db.session.query(QuizResult, Quiz)
        .join(Quiz, QuizResult.quiz_id == Quiz.id)
        .filter(QuizResult.user_id == user_id)
        .order_by(QuizResult.quiz_attempt_date)
        .all()
    )

    # Handle case where no attempts exist
    if not attempts:
        flash("No Records Found", 'info')
        return redirect(url_for("user_dashboard"))

    # Calculate percentages from raw marks
    quiz_names = [quiz.title for _, quiz in attempts]
    scores_percent = [(attempt.score / attempt.total_marks) * 100 for attempt, _ in attempts]

    # Calculate overall average percentage
    avg_score = round(sum(scores_percent) / len(scores_percent), 2)

    # Plot the graph
    plt.figure(figsize=(10, 5))
    plt.bar(quiz_names, scores_percent, color='skyblue')
    plt.xlabel("Quizzes")
    plt.ylabel("Scores (%)")
    plt.title("Quiz Scores")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot in static folder
    graph_dir = "static/graph"
    os.makedirs(graph_dir, exist_ok=True)

    graph_filename = f"user_graph_{user_id}.png"
    graph_path = os.path.join(graph_dir, graph_filename)
    plt.savefig(graph_path)
    plt.close()

    return render_template('user_side/user_summary.html', avg_score=avg_score, graph_url=url_for('static', filename=f'graph/{graph_filename}'))

#user profile update route
@app.route('/user/profile', methods=['GET', 'POST'])
@user_required
def user_profile():
    user = User.query.get(session['id'])
    if request.method == 'POST':
        cpassword = request.form.get('cpassword')
        name = request.form.get('name')
        dob = request.form.get('dob')
        qualification = request.form.get('qualification')

        if not all([cpassword, name, dob, qualification]):
            flash('Please fill all the fields', 'danger')
            return redirect(url_for('user_profile'))
        
        if not check_password_hash(user.password, cpassword):
            flash('Incorrect Current Password', 'danger')
            return redirect(url_for('user_profile'))
        
        if name == user.name and dob == user.dob and qualification == user.qualification:
            flash('No changes found', 'info')
            return redirect(url_for('user_profile'))
        
        session['name'] = name
        user.name = name
        user.dob = dob
        user.qualification = qualification
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('user_profile'))

    return render_template("user_side/user_profile.html", user=user)

#start quiz route
@app.route('/quiz/start/<int:quiz_id>')
@user_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    user_id = session.get('id')
    questions = Question.query.filter_by(chapter_id=quiz.chapter_id)

    # Check if the user has already attempted the quiz
    attempt = QuizResult.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
    if attempt:
        flash("You have already attempted this quiz.", "danger")
        return redirect(url_for('user_dashboard'))
    return render_template("user_side/start_quiz.html", quiz=quiz, questions=questions)

# submit quiz route
@app.route('/submit/quiz/<quiz_id>', methods=['POST'])
@user_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    user_id = session.get('id')

    if not user_id:
        flash("You must be logged in to submit the quiz.", "danger")
        return redirect(url_for('login'))

    # Check if the user has already submitted this quiz
    existing_attempt = QuizResult.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
    if existing_attempt:
        flash("You have already submitted this quiz.", "warning")
        return redirect(url_for('user_dashboard'))

    # Fetch questions and calculate total marks
    questions = Question.query.filter_by(chapter_id=quiz.chapter_id).all()
    total_marks = sum(q.marks for q in questions)

    # Create a new attempt entry
    attempt = QuizResult(
        user_id=user_id,
        quiz_id=quiz.id,
        score=0,
        total_marks=total_marks,
        total_questions=len(questions)
    )
    db.session.add(attempt)
    db.session.flush()  # Flush to get attempt ID without committing fully

    score = 0
    user_answers = []  # Collect all answers first

    # Process each question's answer
    for question in questions:
        user_answer = request.form.get(f'question_{question.id}')
        
        # Ensure the answer is saved even if it's wrong or missing
        user_answers.append(
            UserAnswer(
                user_id=user_id,
                quiz_id=quiz.id,
                question_id=question.id,
                selected_option=user_answer if user_answer else "Not Answered"
            )
        )

        # Score calculation (only if answer is correct)
        if user_answer and str(user_answer) == str(question.correct_option):
            score += question.marks

    # Bulk insert all answers at once (better performance)
    db.session.bulk_save_objects(user_answers)

    # Update attempt with final score
    attempt.score = score
    db.session.commit()

    # Calculate percentage and show results
    percentage_score = (score / total_marks) * 100
    flash(f"Quiz submitted successfully! You scored {score} out of {total_marks} ({percentage_score:.2f}%)", "success")
    return redirect(url_for('user_dashboard'))

# View attempted quiz route
@app.route('/user/view/quiz/<quiz_id>')
@user_required
def view_attempted_quiz(quiz_id):
    user_id = session.get('id')
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(chapter_id=quiz.chapter_id).all()

    # Fetch the user's attempt for this quiz
    attempt = QuizResult.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
    if not attempt:
        flash("You have not attempted this quiz yet.", "danger")
        return redirect(url_for('user_dashboard'))

    # Fetch user's answers for this quiz
    user_answers = UserAnswer.query.filter_by(user_id=user_id, quiz_id=quiz_id).all()

    # Create a dictionary to map question_id to selected_option
    answers_dict = {answer.question_id: answer.selected_option for answer in user_answers}

    # Add selected_option to each question object
    for question in questions:
        question.selected_option = answers_dict.get(question.id, "Not Answered")

    return render_template(
        "user_side/view_attempted_quiz.html",
        quiz=quiz,
        questions=questions,
        attempt=attempt
    )

# Forget password route
@app.route('/forget/password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        dob = request.form.get('dob').strip()
        password = request.form.get('password').strip()

        if not all([username, dob, password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('forget_password'))

        user = User.query.filter_by(username=username).first()
        if not user:
            flash('User does not exist', 'danger')
            return redirect(url_for('forget_password'))
        
        if user.dob != dob:
            flash('Date of birth is incorrect', 'danger')
            return redirect(url_for('forget_password'))

        user.password = generate_password_hash(password)
        db.session.commit()
        flash('Password updated successfully', 'success')
        return redirect(url_for('login'))

    return render_template('forget_password.html')

# Search Function for admin
@app.route("/search/result", methods=["POST"])
@admin_required
def admin_search_result():
    query = request.form.get("search", "").strip()
    results = {}

    if query:
        search_query = f"%{query}%"

        # Fetch users (both admin and non-admin)
        users = User.query.filter(User.username.ilike(search_query) | User.name.ilike(search_query)).all()

        # Fetch quiz attempts **only for non-admin users**
        user_attempts = {
            user.id: QuizResult.query.filter_by(user_id=user.id).all()
            for user in users if not user.is_admin
        }

        results = {
            "users": users,
            "user_attempts": user_attempts,
            "subjects": Subject.query.filter(Subject.sub_name.ilike(search_query) | Subject.subjectId.ilike(search_query)).all(),
            "chapters": Chapter.query.filter(Chapter.chapter_name.ilike(search_query) | Chapter.chapterId.ilike(search_query)).all(),
            "quizzes": Quiz.query.filter(Quiz.title.ilike(search_query) | Quiz.quizId.ilike(search_query)).all(),
        }
    return render_template("admin_side/search_result.html", results=results, search_query=query)

# Search Function for user
@app.route('/user/search/result', methods=['POST'])
@user_required
def user_search_result():
    user_id = session.get('id')
    search = request.form.get('search', "").strip()
    results = {}

    now = datetime.now()

    if search:
        # Search quizzes by title
        quizzes = Quiz.query.filter(Quiz.title.ilike(f"%{search}%")).all()

        # Search subjects and fetch quizzes related to those subjects
        subjects = Subject.query.filter(Subject.sub_name.ilike(f"%{search}%")).all()
        subject_quizzes = (
            Quiz.query.join(Subject)
            .filter(Subject.sub_name.ilike(f"%{search}%"))
            .all()
        )

        # Search chapters and fetch quizzes related to those chapters
        chapters = Chapter.query.filter(Chapter.chapter_name.ilike(f"%{search}%")).all()
        chapter_quizzes = (
            Quiz.query.join(Chapter)
            .filter(Chapter.chapter_name.ilike(f"%{search}%"))
            .all()
        )

        # Combine all unique quizzes
        all_quizzes = list(set(quizzes + subject_quizzes + chapter_quizzes))

        results = {
            "quizzes": all_quizzes
        }

    # Get the list of quiz IDs the user has attempted
    quiz_attempt_ids = [attempt.quiz_id for attempt in QuizResult.query.filter_by(user_id=user_id).all()]

    return render_template('user_side/search_result.html', results=results, quiz_attempt_ids=quiz_attempt_ids, search=search, now=now)

#users who attempt the quiz
@app.route('/admin/quiz/<int:quiz_id>/attempted')
@admin_required
def attempted_users(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    # Fetch users with their scores for this quiz
    users_attempted = (
        db.session.query(User, QuizResult.score, QuizResult.total_marks)
        .join(QuizResult, User.id == QuizResult.user_id)
        .filter(QuizResult.quiz_id == quiz_id)
        .all()
    )

    return render_template(
        'admin_side/attempted_users.html', quiz=quiz, users_attempted=users_attempted)

#users who not attempt the quiz
@app.route('/admin/quiz/<int:quiz_id>/not_attempted')
@admin_required
def not_attempted_users(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    # Fetch all users
    all_users = User.query.filter(User.is_admin == False).all()

    # Fetch users who attempted the quiz
    attempted_users_ids = (
        db.session.query(QuizResult.user_id)
        .filter(QuizResult.quiz_id == quiz_id)
        .all()
    )
    attempted_users_ids = {user_id[0] for user_id in attempted_users_ids}

    # Get users who didn't attempt the quiz
    not_attempted = [user for user in all_users if user.id not in attempted_users_ids]

    return render_template(
        'admin_side/not_attempted_users.html', quiz=quiz, users=not_attempted)

# Route to view all users
@app.route('/admin/user/list')
@admin_required
def user_list():
    users = User.query.filter(User.is_admin == False).all()
    return render_template('admin_side/user_list.html', users=users)