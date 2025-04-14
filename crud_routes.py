from flask import Flask, render_template, request, flash, redirect, url_for, session
from app import app
from models import db, Subject, Chapter, Question, Quiz, User, QuizResult, UserAnswer
from routes import user_required, admin_required
from datetime import datetime
import json

# ----------Admin CRUD routes----------

# Add subject route
@app.route('/admin/add_subject', methods=['GET', 'POST'])
@admin_required
def add_subject():
    if request.method == 'POST':
        subject_Id = request.form.get('subjectId', '').strip()
        sub_name = request.form.get('subjectName', '').strip()
        description = request.form.get('description')

        if not all([subject_Id, sub_name]):
            flash('All fields are required!', 'danger')
            return redirect(url_for('add_subject'))

        subjectId = Subject.query.filter_by(subjectId=subject_Id).first()
        subjectName = Subject.query.filter_by(sub_name=sub_name).first()
        if subjectId or subjectName:
            flash('Subject already exists!', 'danger')
            return redirect(url_for('add_subject'))
        
        new_subject = Subject(subjectId=subject_Id, sub_name=sub_name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        flash('Subject added successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_side/crud_temp/add_subject.html')

# edit subject route
@app.route('/admin/edit/subject/<int:subject_id>', methods=['GET', 'POST'])
@admin_required
def edit_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        flash('Subject not found', 'info')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        subject_Id = request.form.get('subjectId', '').strip()
        subject_name = request.form.get('subjectName', '').strip()
        description = request.form.get('description')

        subject.subjectId = subject_Id
        subject.sub_name = subject_name
        subject.description = description
        db.session.commit()
        flash('Subject updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_side/crud_temp/edit_subject.html', subject=subject)

# delete subject route
@app.route('/admin/delete/<int:subject_id>', methods=['GET','POST'])
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get(subject_id)

    #check if subject has any related quiz 
    quizzes = Quiz.query.filter_by(subject_id=subject_id).all()
    if quizzes:
        flash('Error deleting subject. Make sure there are no related quizzes.', 'info')
        return redirect(url_for('admin_dashboard'))

    #delete related chapters
    for chapter in subject.chapters:
        db.session.delete(chapter)
        db.session.commit()

    try:
        db.session.delete(subject)
        db.session.commit()
        flash('Subject deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting subject. Make sure there are no related chapters.', 'danger')
    return redirect(url_for('admin_dashboard'))

# Add chapter route
@app.route('/admin/add_chapter/<int:subject_id>', methods=['GET', 'POST'])
@admin_required
def add_chapter(subject_id):
    subject = Subject.query.get(subject_id)
    if request.method == 'POST':
        chapter_Id = request.form.get('chapterId', '').strip()
        chapter_name = request.form.get('chapterName', '').strip()
        description = request.form.get('description')

        chapterId = Chapter.query.filter_by(chapterId=chapter_Id, subject_id=subject_id).first()
        chapterName = Chapter.query.filter_by(chapter_name=chapter_name, subject_id=subject_id).first()
        if chapterId or chapterName:
            flash('Chapter already exists!', 'danger')
            return redirect(url_for('add_chapter'))
        
        new_chapter = Chapter(chapterId=chapter_Id,chapter_name=chapter_name, description=description, subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()
        flash('Chapter added successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_side/crud_temp/add_chapter.html', subject=subject)

# delete chapter route
@app.route('/admin/delete_chapter/<int:chapter_id>', methods=['GET','POST'])
@admin_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    #check if chapter has any related quiz
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    if quizzes:
        flash('Error deleting chapter. Make sure there are no related quizzes.', 'info')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

# edit chapter route
@app.route('/admin/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
@admin_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if request.method == 'POST':
        chapter_Id = request.form.get('chapterId', '').strip()
        chapter_name = request.form.get('chapterName', '').strip()
        description = request.form.get('description')

        chapter.chapterId = chapter_Id
        chapter.chapter_name = chapter_name
        chapter.description = description
        db.session.commit()
        flash('Chapter updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_side/crud_temp/edit_chapter.html', chapter=chapter)

# Add question route
@app.route('/admin/add_question/<int:chapter_id>', methods=['GET', 'POST'])
@admin_required
def add_question(chapter_id):
    if request.method == 'POST':
        question_Id = request.form.get('questionId', '').strip()
        question = request.form.get('question', '').strip()
        option1 = request.form.get('option1', '').strip()
        option2 = request.form.get('option2', '').strip()
        option3 = request.form.get('option3', '').strip()
        option4 = request.form.get('option4', '').strip()
        answer = request.form.get('answer', '').strip()
        marks = request.form.get('marks', '').strip()

        if not all([question_Id, question, option1, option2, option3, option4, answer, marks]):
            flash('All fields are required', 'danger')
            return redirect(url_for('add_question', chapter_id=chapter_id))

        questionId = Question.query.filter_by(questionId=question_Id).first()
        if questionId:
            flash('Question Id already exists!', 'danger')
            return redirect(url_for('add_question', chapter_id=chapter_id))

        new_question = Question(questionId=question_Id, title=question, option1=option1, option2=option2, option3=option3, option4=option4, correct_option=answer, marks=marks, chapter_id=chapter_id)
        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully', 'success')
        return redirect(url_for('add_question', chapter_id=chapter_id))
    return render_template('admin_side/crud_temp/add_question.html', chapter_id=chapter_id)

# View questions route
@app.route('/admin/view/questions/<int:chapter_id>', methods=['GET','POST'])
@admin_required
def view_questions(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    questions = Question.query.filter_by(chapter_id=chapter_id).all()
    return render_template('admin_side/crud_temp/view_question.html', chapter=chapter, questions=questions)

# Edit question route
@app.route('/admin/edit/question/<int:question_id>', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    question = Question.query.get(question_id)

    if not question:
        flash("Question not found!", "danger")
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        question.questionId = request.form.get('questionId', question.questionId)
        question.title = request.form.get('question', question.title)
        question.option1 = request.form.get('option1', question.option1)
        question.option2 = request.form.get('option2', question.option2)
        question.option3 = request.form.get('option3', question.option3)
        question.option4 = request.form.get('option4', question.option4)
        question.correct_option = request.form.get('answer', question.correct_option)
        question.marks = request.form.get('marks', question.marks)
        try:
            db.session.commit()
            flash("Question updated successfully!", "success")
            return redirect(url_for('view_questions', chapter_id=question.chapter_id))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the question.", "danger")

    return render_template('admin_side/crud_temp/edit_question.html', question=question)

# Delete question route
@app.route('/admin/delete_question/<int:question_id>', methods=['GET','POST'])
@admin_required
def delete_question(question_id):
    question = Question.query.get(question_id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully', 'success')
    return redirect(url_for('view_questions', chapter_id=question.chapter_id))

# Create Quiz route
@app.route('/admin/create/quiz', methods=['GET', 'POST'])
@admin_required
def create_quiz():
    if request.method == 'POST':
        quiz_Id = request.form.get('quizId', '').strip()
        title = request.form.get('title', '').strip()
        description = request.form.get('description')
        subject_id = request.form.get('subject')
        chapter_id = request.form.get('chapter')
        num_questions = request.form.get('num_questions')
        duration = request.form.get('duration')
        due_date_str = request.form.get('due_date')

        quizId = Quiz.query.filter_by(quizId=quiz_Id).first()
        if quizId:
            flash('Quiz Id already exists!', 'danger')
            return redirect(url_for('create_quiz'))
        
        exist_subject_id = Quiz.query.filter_by(subject_id=subject_id).first()
        exist_chapter_id = Quiz.query.filter_by(chapter_id=chapter_id).first()
        if exist_subject_id and exist_chapter_id:
            flash('Quiz already exist!', 'danger')
            return redirect(url_for('create_quiz'))
        
        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')

        # Creating new quiz
        new_quiz = Quiz(quizId=quiz_Id, title=title, description=description, subject_id=subject_id, chapter_id=chapter_id, number_of_questions=num_questions, duration=duration, due_date=due_date)
        db.session.add(new_quiz)
        db.session.commit()
        flash('Quiz created successfully!', 'success')
        return redirect(url_for('view_quizzes'))

    subjects = Subject.query.all()
    chapters = {
        subject.id: [{"id": ch.id, "name": ch.chapter_name, "question_count": len(ch.questions)} for ch in subject.chapters]
        for subject in subjects
    }

    return render_template('admin_side/crud_temp/create_quiz.html', subjects=subjects, chapters=json.dumps(chapters))


# edit quiz
@app.route('/edit/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    subjects = Subject.query.all()

    if request.method == 'POST':
        quiz_Id = request.form.get('quizId', '').strip()
        title = request.form['title']
        description = request.form['description']
        subject_id = request.form['subject']
        chapter_id = request.form['chapter']
        num_questions = request.form['num_questions']
        duration = request.form['duration']
        due_date_str = request.form['due_date']

        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')

        # Updating quiz details
        quiz.quizId = quiz_Id
        quiz.title = title
        quiz.description = description
        quiz.subject_id = subject_id
        quiz.chapter_id = chapter_id
        quiz.number_of_questions = num_questions
        quiz.duration = duration
        quiz.due_date = due_date

        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('view_quizzes'))

    return render_template('admin_side/crud_temp/edit_quiz.html', quiz=quiz, subjects=subjects)

# Route to delete a quiz
@app.route('/admin/delete_quiz/<int:quiz_id>', methods=['POST'])
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.is_deleted = True
    db.session.commit()
    flash("Quiz deleted successfully!", "success")
    return redirect(url_for('view_quizzes'))

# Routes for permanent delete a quiz
@app.route('/admin/permanent_delete_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
def permanently_delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    # delete quiz from QuizResult table
    quiz_results = QuizResult.query.filter_by(quiz_id=quiz_id).all()
    for quiz_result in quiz_results:
        db.session.delete(quiz_result)
    # delete quiz from UserAnswer table
    user_answers = UserAnswer.query.filter_by(quiz_id=quiz_id).all()
    for user_answer in user_answers:
        db.session.delete(user_answer)
    # delete quiz from Quiz table
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz permanently deleted successfully!", "success")
    return redirect(url_for('view_quizzes'))

# Route for reactive a quiz
@app.route('/admin/reactive_quiz/<int:quiz_id>', methods=['POST'])
@admin_required
def reactive_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.is_deleted = False
    db.session.commit()
    flash("Quiz reactivated successfully!", "success")
    return redirect(url_for('view_quizzes'))

# route for delete user
@app.route('/admin/delete_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # delete user from QuizResult table
    quiz_results = QuizResult.query.filter_by(user_id=user_id).all()
    for quiz_result in quiz_results:
        db.session.delete(quiz_result)
    # delete user from UserAnswer table
    user_answers = UserAnswer.query.filter_by(user_id=user_id).all()
    for user_answer in user_answers:
        db.session.delete(user_answer)
    # delete user from User table
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for('user_list'))