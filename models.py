from flask_sqlalchemy import SQLAlchemy
from app import app
from datetime import datetime

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(10), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subjectId = db.Column(db.String(50), nullable=False, unique=True)
    sub_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    #relationship
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")
    

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chapterId = db.Column(db.String(50), nullable=False)
    chapter_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    #foreign-key
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    #relationship for question
    questions = db.relationship('Question', backref='chapter', lazy=True, cascade="all, delete-orphan")


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questionId = db.Column(db.String(50), nullable=False)
    title = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)
    marks = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    #foreign-key
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quizId = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=True)
    number_of_questions = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    is_deleted = db.Column(db.Boolean, nullable=False, default=False) 

    #foreign-key
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)

    #relationship
    subject = db.relationship('Subject', backref='quizzes', lazy="joined")
    chapter = db.relationship('Chapter', backref='quizzes', lazy="joined")

    # Soft delete
    def soft_delete(self):
        """Mark the quiz as deleted."""
        self.is_deleted = True
        db.session.commit()


class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    quiz_attempt_date = db.Column(db.DateTime, default=datetime.now)

    #foreign-key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

    #relationship
    quiz = db.relationship('Quiz', backref='answer', lazy=True)

class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    selected_option = db.Column(db.String(1), nullable=False)

    # foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

    # relationships
    user = db.relationship('User', backref='answers', lazy=True)
    question = db.relationship('Question', backref='answers', lazy=True)
    quiz = db.relationship('Quiz', backref='answers', lazy=True)

with app.app_context():
    db.create_all()
