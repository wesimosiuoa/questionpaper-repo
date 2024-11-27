from . import app
from flask import Blueprint, send_file, render_template, request, redirect, url_for, flash, session,send_from_directory
from .dbcon import get_connection
from .models import *
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# app = Blueprint('main', __name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/features', methods=['GET', 'POST'])
def features():
    return render_template('features.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST': 
        email = request.form.get('email')
        pwd = request.form.get('password')

        try: 
            connection = get_connection()

            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users inner join roles on users.role_id = roles.role_id WHERE users.email = %s", (email,))
                user = cursor.fetchone()
                # print ('User : ', user['role_id'])
                if user : 
                    stored_pass = user['pwd']
                    if pwd == stored_pass : 
                        session['username'] = email
                        session['id'] = user['user_id']
                        session['fullname'] = user['fullname']
                        
                        role_name = user['role_name']
                        #username = user['fullname']
                        # print ('Role : ', user['role_id'])
                        if user['role_id'] == 1: 
                            
                            # flash (f"Hey {username}, Login successful, you are  {role_name}", 'success')
                            return redirect(url_for('student_panel'))
                            
                        elif user['role_id'] == 2: 
                            return redirect (url_for('teacher_panel'))
                            # flash (f" Hey {username}, Login successful, you are {role_name}", 'success')
                        elif user['role_id'] == 3: 
                            return redirect (url_for('admin_panel'))
                            # flash (f" Hey {username}, Login successful, you are {role_name}", 'success') 
                        else :
                            print(f" Role {role_name} does not exists", 'danger')
                        
                    else : 
                        flash (" Incorrect login details", 'danger')
                else : 
                    flash ('User not found ')
        except Exception as e: 
            # flash ('There was and error in searching for a user ', 'danger')
            print (f"Error : {e}")
    # return render_template ('logi')
    return render_template('login.html')

@app.route ('/student_panel')
def student_panel():
    connection = get_connection()
    upcoming_tasks = []

    try: 
        with connection.cursor() as cursor: 
            cursor.execute ('select * from questionpapers order by paper_id desc limit 3;')
            upcoming_tasks = cursor.fetchall()
            print (f' Tasks : ',upcoming_tasks)
    except Exception as e: 
        flash (f" Error : {e}", 'danger')
        print (f' Error : {e}')
    finally : 
        connection.close()
    return render_template ('student-panel.html', upcoming_tasks = upcoming_tasks)
    # return render_template ('student-panel.html')
@app.route('/teacher_panel')
def teacher_panel(): 

    connection = get_connection ()
    try: 
        with connection.cursor() as cursor: 
            sql = 'SELECT count(paper_id) as numer_questions from questionpapers where uploaded_by = %s;'
            cursor.execute (sql, ( session['id'],))
            result = cursor.fetchall ()[0]
            number_of_question_papers = result['numer_questions']
            sql = "SELECT count(submissions.submission_id) as _submitted_question_papers from submissions inner join questionpapers on submissions.paper_id = questionpapers.paper_id INNER JOIN courses on questionpapers.course_id = courses.course_id where submissions.status = 'submitted' and courses.user_id = %s;"
            cursor.execute(sql, (session['id'], ))
            result = cursor.fetchall()[0]
            _submitted_question_papers = result['_submitted_question_papers']
            sql = "SELECT count(submissions.submission_id) as _pending_question_papers from submissions inner join questionpapers on submissions.paper_id = questionpapers.paper_id INNER JOIN courses on questionpapers.course_id = courses.course_id where submissions.status = 'awaiting grading' and courses.user_id = %s;"
            cursor.execute(sql, (session['id'], ))
            result = cursor.fetchall()[0]
            _pending_question_papers = result['_pending_question_papers']
    except Exception as e: 
        flash ('Failed to get number of question papers ', 'danger')
        print (' Error : ', e)
        number_of_question_papers = 0
        _submitted_question_papers = 0
    finally: 
        connection.close()
    return render_template ('teacher-panel.html', _submitted_question_papers=_submitted_question_papers, number_of_question_papers = number_of_question_papers)

@app.route('/admin_panel')
def admin_panel(): 
    if 'username' not in session: 
        flash ('You need to login to access this page', 'danger')
        return redirect (url_for('login'))
    return render_template ('admin-panel.html')

@app.route ('/users')
def users():
    connection = get_connection()  # Assuming this function is defined elsewhere
    try:
        sql = "SELECT * FROM users INNER JOIN roles ON users.role_id = roles.role_id"
        with connection.cursor() as cursor:  # Use cursor() instead of cursor
            cursor.execute(sql)
            users = cursor.fetchall()  
    except Exception as e: 
        flash('Failed to retrieve users', 'danger')
        print(f"Error: {e}")  # Print error message for debugging
    finally: 
        connection.close()  # Ensure the connection is closed

    return render_template('users.html', users=users)  # Use 'users' instead of 'user'

@app.route('/add_user', methods = ['GET', 'POST'])
def add_user ():
    if request.method == 'POST': 
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        pwd = request.form.get('password')
        role_id = request.form.get('role')
        new_user = User(fullname=fullname, email=email, pwd=pwd, role_id=role_id)
        
        try:
            connection = get_connection ()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash('Email already registered. Please use a different email.', 'danger')
                    return redirect(url_for('users'))
            
                sql = "INSERT INTO `users` (`user_id`, `fullname`, `email`, `pwd`, `role_id`) VALUES (NULL, %s, %s, %s, %s);" 
                
                cursor.execute (sql, (new_user.fullname, new_user.email, new_user.pwd, new_user.role_id))
                connection.commit()
                flash ('New user recorded successfully ', 'success')
                return redirect(url_for('users'))

        except Exception as e : 
            flash ('Failed to add user ', 'success')
            print (f" Error : {e}")
        finally: 
            connection.close()

        # return f"{fullname} {email} {pwd} {role}"
@app.route('/logout')
def logout ():
    session.pop('username', None)
    session.pop('id', None)
    session.pop('Fullname', None)
    session.clear()
    return redirect(url_for('login'))
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('name')
        email = request.form.get('email')
        pwd = request.form.get('password')
        role_number = 1
        new_user = User(fullname=fullname, email=email, pwd=pwd, role_id=role_number)

        # Insert user into the database
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash('Email already registered. Please use a different email.', 'danger')
                    return redirect(url_for('register'))
            
                sql = "INSERT INTO users (fullname, email, pwd, role_id) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (new_user.fullname, new_user.email, new_user.pwd, new_user.role_id))
                connection.commit()
            flash('Successfully registered', 'success')
            return redirect(url_for('register'))
        except Exception as e:
            flash('There was an error when adding the new user ', 'danger')
            print(e)
        finally:
            connection.close()

    return render_template('register.html')

@app.route('/delete_user', methods=['GET', 'POST'])
def delete_user():

    user_id = request.args.get('user_id')
    if user_id is None: 
        flash ('User not provided ', 'danger')
        return redirect (url_for ('users'))
    try: 
        connection = get_connection()
        with connection.cursor() as cursor:
            sql = ' delete from users where user_id = %s'
            cursor.execute (sql, (user_id, ))
            connection.commit()

            flash (f' User ID {user_id} deleted successfully ', 'success')
            return redirect (url_for ('users')) 
    except Exception as e : 
        flash (' Failed to delete user ', 'danger')
        print (f" Error {e}")
    finally: 
        connection.close()

@app.route ('/get_user')

def get_user ():
    user_id = request.args.get('user_id')  # Get user_id from query string
    connection = get_connection()

    try:
        with connection.cursor() as cursor:  # Note the missing parentheses in your original code
            sql = 'SELECT * FROM users WHERE user_id = %s'
            cursor.execute(sql, (user_id,))
            user = cursor.fetchone()  # Fetch the user data

        if user:
            # Pass the user data to the template using render_template
            return render_template('update.html', user=user)
        else:
            flash(f'No user found with ID {user_id}', 'danger')
            return redirect(url_for('users'))  # Redirect to user management if no user is found
    except Exception as e:
        flash('Failed to retrieve user information', 'danger')
        print(f'Error: {e}')
        return redirect(url_for('users'))  # Redirect on error
    finally:
        connection.close() 

# course 
@app.route('/get_teacher', methods=['GET', 'POST'])
@app.route('/get_teacher', methods=['GET', 'POST'])
def get_teacher():
    connection = get_connection()  # Assuming this function is defined elsewhere
    try:
        with connection.cursor() as cursor:
            sql = '''SELECT courses.course_id, courses.title, courses.description, courses.created_at, users.fullname 
                     FROM courses 
                     INNER JOIN users ON courses.user_id = users.user_id'''
            cursor.execute(sql)
            courses = cursor.fetchall()
            print(courses)  # Debugging output to ensure correct data is fetched
    except Exception as e:
        flash('Failed to retrieve data', 'danger')
        print(f"Error: {e}")  # Debugging information
    finally:
        connection.close()  # Ensure the connection is closed
    
    return render_template('course-management.html', courses=courses)
@app.route ('/courses', methods = ['GET', 'POST'])




        
@app.route ('/get_course', methods=['GET', 'POST'])
def get_course ():
    connection = get_connection()
    with connection.cursor() as cursor : 
        try: 
            sql = 'select * from courses inner join users on courses.user_id = users.user_id'
            cursor.execute(sql)
            courses = cursor.fetchall()

            sql = "SELECT * FROM users INNER JOIN roles ON users.role_id = roles.role_id where users.role_id = 2 "
        # with connection.cursor() as cursor:  # Use cursor() instead of cursor
            cursor.execute(sql)
            users = cursor.fetchall()
        except Exception as e : 
            print (e)
        finally: 
            connection.close () 

    return render_template ('course-management.html', courses=courses, users = users)
@app.route('/delete_course', methods=['GET', 'METHODS'])
def delete_course ():
    course_id = request.args.get('course_id')
    connection = get_connection ()

    try: 
        with connection.cursor() as cursor :
            sql = 'delete from courses where course_id = %s'
            cursor.execute (sql, (course_id,))
            connection.commit()
        
        flash (' Success : Course deleted successfully ', 'success')
    except Exception as e: 
        flash ('Failed to delete ', 'danger')
        print (f" Error {e}")
    return redirect (url_for ('get_teacher'))


@app.route ('/new_course', methods=['GET', 'POST'])
def new_course (): 
    connection = get_connection ()
    sql = ' select user_id, fullname from users where role_id = 2 '
    try: 
        with connection.cursor() as cursor :
            cursor.execute (sql)
            users = cursor.fetchall()
    except Exception as e:
        flash (' Failed to retrive user ' , 'danger') 
        print (f' Error : {e}' )
    finally: 
        connection.close()

    return render_template ('add-course.html', users = users )

@app.route ('/record_course_in_db', methods=['GET', 'POST'])
def record_course_in_db():
    if request.method == 'POST':
        
        title = request.form.get('title')
        description = request.form.get('description')
        teacher = request.form.get('user_id')
        new_course = Course (title = title, description = description,teacher = teacher )
        connection = get_connection()
        try: 
        
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM courses WHERE title = %s", (title,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash('Course already registered. Please use a different course title.', 'danger')
                    return redirect(url_for('get_teacher'))
                sql = 'INSERT INTO `courses` (`course_id`, `title`, `description`, `user_id`, `created_at`) VALUES (NULL, %s, %s, %s, current_timestamp());'
                cursor.execute (sql, (new_course.title, new_course.description, new_course.teacher))
                connection.commit()
            flash ('New course recorded successfully ', 'success')
        except Exception as e : 
            flash (' Failed to record course ', 'danger')
            print (f"Error : {e}")
        finally :
            connection.close()

        return redirect(url_for ('get_teacher'))
    return 'Method Not allowed ', 405


@app.route ('/upload', methods=['GET', 'POST'])
def upload(): 

    user_id = session['id']
    connection = get_connection ()
    courses = []
    try: 
        with connection.cursor() as cursor: 
            sql = 'SELECT * from courses where user_id = %s'
            cursor.execute (sql, (user_id, ))
            courses = cursor.fetchall ()
            print (courses)
    except Exception as e : 

        flash (' Failed to retrieve courses ', 'danger')
        print(f"Error ", e)
    finally: 
        connection.close()
    return render_template ('upload-question.html', courses = courses)



ALLOWED_EXTENSIONS = {'pdf'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 

def unique_filename (filename, ALLOWED_EXTENSIONS):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_name =  f"{filename.rsplit('.', 1)[0]}_{timestamp}.{ALLOWED_EXTENSIONS}"
    return unique_name

@app.route('/upload_question', methods= ['GET', 'POST'])
def upload_question(): 
    
    if request.method == 'POST': 
        uploaded_by = session['id']
        title = request.form.get ('title')
        grade = request.form.get('grade')
        category = request.form.get('category')
        course_id = request.form.get('course_id')
        instruction = request.form.get('instruction')
        date = request.form.get('date')
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']

        if not file or not allowed_file(file.filename):
            flash('Invalid file format. Please upload a PDF.', 'danger')
            return redirect(request.url)
        if file.filename == '':
            flash ('File no specified ')
            return False   
        if file:
            # Save the file to the UPLOAD_FOLDER defined in the config
            unique_name = unique_filename(file.filename, 'pdf')
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            print (f" Try this " , app.config['UPLOAD_FOLDER'])
            file.save(filepath)
            # return f"File {file.filename} uploaded successfully to {app.config['UPLOAD_FOLDER']}!"
        filename = unique_name

        new_question = question_papers (title = title, category = category, instruction = instruction, grade = grade, uploaded_by = uploaded_by, course_id =  course_id, file = filename, date = date)
        connection = get_connection ()
        try:
            with connection.cursor() as cursor : 
                sql =  'INSERT INTO `questionpapers` (`paper_id`, `title`, `category`, `instructions`, `grade_level`, `uploaded_by`, `course_id`, `created_at`, `file`, `deadline`) VALUES (NULL, %s, %s, %s, %s, %s, %s, current_timestamp(), %s, %s);'
                cursor.execute(sql, (new_question.title, new_question.category, new_question.instruction, new_question.grade, new_question.uploaded_by, new_question.course_id, new_question.file, new_question.date))
                connection.commit()
            flash ('Question Paper uploaded ', 'success')
        except Exception as e : 
            flash ('Failed to upload questio paper, Try Again ', 'danger')
            print (' Error ', e)
        finally: 
            connection.close()
    return redirect ('upload')

@app.route('/uploaded_questions', methods=['GET', 'POST'])
def uploaded_questions(): 
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    uploaded_questions = []
    connection = get_connection()
    try:
        with connection.cursor() as cursor: 
            sql = 'select * from questionpapers inner join users on questionpapers.uploaded_by = users.user_id inner join courses on courses.course_id  = questionpapers.course_id where uploaded_by = %s'
            cursor.execute (sql, (session['id'], ))
            uploaded_questions = cursor.fetchall()
    except Exception as e : 
        flash ('Failed to get question papers ', 'danger')
        print (' Error ', e)
    finally: 
        connection.close()
    return render_template ('uploaded_questions.html', question_papers = uploaded_questions, uploaded_files = uploaded_files)


@app.route('/download/<filename>', methods=['GET', 'POST'])
def download(filename): 
    
    dir = './uploads/'
    return send_file (dir + filename, mimetype='application/pdf')

@app.route ('/_download_submission/<filename>', methods=['GET', 'POST'])
def _download_submission (filename) :
    submission_number = request.args.get('submission_number')
    connection = get_connection ()
    try:
        with connection.cursor() as cursor : 
            sql = "UPDATE submissions set submissions.status = 'awaiting grading' where submissions.submission_id = 2;"
            cursor.execute (sql, (submission_number,))
            connection.commit()
    except Exception as e : 
        print (f' Error : failed to update submission {e}')
    finally: 
        connection.close()
    dir = './submissions/'
    return send_file (dir + filename, mimetype='application/pdf')
    # return f'Update successful'

@app.route('/download_submission/<filename>', methods=['GET', 'POST'])
def download_submission(filename): 
    dir = './submissions/'
    return send_file (dir + filename, mimetype='application/pdf')

@app.route('/delete_question_paper', methods=['GET', 'POST'])
def delete_question_paper(): 
    question_paper = request.args.get('question_paper')
    connection = get_connection()
    print (' Question Paper : ', question_paper )
    print (' User :     ', session['id'])

    try:
        # Corrected cursor usage
        with connection.cursor() as cursor: 
            sql = 'DELETE FROM `questionpapers` WHERE `questionpapers`.`file` = %s and `questionpapers`.`uploaded_by` = %s;'
            print (f' Executing : {sql}')
            cursor.execute(sql, (question_paper, session['id']))
            connection.commit()
            dir = '/uploads/'
            file_path = os.path.join(dir, question_paper)
            print (f' Path : ', file_path)

            try:
                if os.path.exists(file_path): 
                    os.remove(file_path)
                
            except Exception as e : 
                print (f' Error : {e}')

        flash('File deleted successfully', 'success')
        print("File deleted successfully")

    except Exception as e:
        flash(f"Error: {e}", 'danger')
        print(f'Error: {e}')

    finally:
        connection.close()

    return redirect(url_for('uploaded_questions'))

@app.route ('/get_question_papers', methods=['GET', 'POST'])
def get_question_papers (): 
    connection = get_connection ()
    question_papers  = []

    try: 
        with connection.cursor() as cursor: 
            cursor.execute ('SELECT `paper_id`, questionpapers.title as papername,  `category`, `fullname`, courses.title as coursename, questionpapers.file, questionpapers.deadline FROM questionpapers INNER JOIN users ON questionpapers.uploaded_by = users.user_id INNER JOIN courses ON questionpapers.course_id = courses.course_id ORDER BY questionpapers.paper_id DESC LIMIT 0, 25;')
            question_papers = cursor.fetchall()
            print (f' Tasks : ',question_papers)
    except Exception as e: 
        flash (f" Error : {e}", 'danger')
        print (f' Error : {e}')
    finally : 
        connection.close()
    return render_template ('student-question-papers.html', question_papers = question_papers)

@app.route('/submission', methods=['GET', 'POST'])
def submission(): 
    connection = get_connection ()
    try: 
        with connection.cursor() as cursor : 
            sql = 'select questionpapers.paper_id, questionpapers.title from questionpapers' 
            cursor.execute(sql)
            question = cursor.fetchall()
    except Exception as e: 
        print (f' Error : {e}')
    finally: 
        connection.close()
    return render_template ('make-submission.html', question=question)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    question_paper = None  # Initialize the variable to avoid UnboundLocalError
    filename = None

    if request.method == 'POST': 
        question_paper = request.form.get('question')
        
        # Check if a file is part of the request
        if 'file' not in request.files:
            flash('No file part in the request', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Validate the file type (only PDFs are allowed in this case)
        if not file or not allowed_file(file.filename):
            flash('Invalid file format. Please upload a PDF.', 'danger')
            return redirect(request.url)
        
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        if file:
            # Save the file with a unique name to avoid conflicts
            dir = './app/submissions/' #dir = './uploads/'
            unique_name = unique_filename(file.filename, 'pdf')
            filepath = os.path.join(dir, unique_name)
            print(f"Saving file to: {dir}")
            file.save(filepath)
            filename = unique_name
    
    # Check if question_paper or filename are None
    # if question_paper and filename:
        student_id = session['id']
        print (f' Student : {student_id}')
        new_submission = Submission (student_id=student_id, paper_id=question_paper, file=filename)
        connection = get_connection()
            
        try: 
            with connection.cursor() as cursor: 
                sql = 'INSERT INTO `submissions` (`submission_id`, `student_id`, `paper_id`, `submitted_at`, `status`, `file_path`) VALUES (NULL, %s, %s, current_timestamp(), %s, %s);'
                cursor.execute(sql, (new_submission.student_id, new_submission.paper_id,'submitted', new_submission.file))
                connection.commit()

            flash ('Your submission is recieved, view your grades from grades panel', 'success')
        except Exception as e: 
            print (f' Error : {e}')
        finally: 
            connection.close()
    # else:
    #     print (f" File not {filename} submitted to question {question_paper}")
    return redirect(url_for ('submission'))

@app.route('/my_submission', methods=['GET', 'POST'])
def my_submission (): 
    connection = get_connection ()
    my_submission = []

    try: 
        with connection.cursor() as cursor:
            sql = ' select * from submissions inner join questionpapers on submissions.paper_id = questionpapers.paper_id where submissions.student_id = %s'
            cursor.execute (sql, (session['id']))
            my_submission = cursor.fetchall ()
    except Exception as e: 
        print (f' Error : {e}')
    finally: 
        connection.close()
    return render_template('student-question-paper.html', my_submission=my_submission)

@app.route ('/_student_submissions', methods = ['GET', 'POST'])
def _student_submissions ():
    connection = get_connection()
    student_submissions = []
    try: 
        with connection.cursor() as cursor : 
            sql = 'SELECT submissions.submission_id, submissions.submitted_at, submissions.student_id, submissions.file_path, questionpapers.title as _questionpaper, courses.title as _course from submissions INNER JOIN questionpapers on submissions.paper_id = questionpapers.paper_id inner join courses on questionpapers.course_id = courses.course_id where courses.user_id = %s;'
            cursor.execute (sql, (session['id']))
            student_submissions = cursor.fetchall()
            
    except Exception as e: 
        print (f" Error : {e}")
    finally: 
        connection.close()
    return render_template ('student_submissions.html', student_submissions = student_submissions)
