from flask import Flask, request, render_template, redirect, url_for, flash, abort, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_wtf.file import FileField, FileRequired, FileAllowed
import os
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)

# Configure the database connection and other settings
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size: 16MB

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Course model
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    videos = db.relationship('Video', backref='course', lazy=True)

    def __repr__(self):
        return f"Course('{self.name}')"

# Video model
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f"Video('{self.title}', '{self.filename}')"



# Registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = StringField('Role', default='user')  # Add a role field to the form
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

# Login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UploadForm(FlaskForm):
    file = FileField('File', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'pdf', 'txt', 'mp4'], 'Files only!')])
    submit = SubmitField('Upload')

class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(min=2, max=150)])
    description = StringField('Description', validators=[DataRequired(), Length(min=2)])
    submit = SubmitField('Create Course')

class VideoForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=2, max=150)])
    course_id = StringField('Course ID', validators=[DataRequired()])
    file = FileField('Video File', validators=[FileRequired(), FileAllowed(['mp4'], 'MP4 files only!')])
    submit = SubmitField('Upload Video')

@app.route('/')
def home():
    courses = Course.query.all()
    return render_template('index.html', title="Home Page", heading="Welcome to My Website", content="This is the home page content.", courses=courses)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    user = User(username=name)
    db.session.add(user)
    db.session.commit()
    return f"User {name} has been added to the database."

@app.route('/users')
@login_required
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin')
@login_required
@role_required('admin')
def admin():
    return "This is the admin page, accessible only to admins."

@app.route('/create_course', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_course():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(name=form.name.data, description=form.description.data)
        db.session.add(course)
        db.session.commit()
        flash('Course has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_course.html', title='Create Course', form=form)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File successfully uploaded', 'success')
        return redirect(url_for('uploaded_files'))
    return render_template('upload.html', title='Upload File', form=form)

@app.route('/upload_video', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def upload_video():
    form = VideoForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        video = Video(title=form.title.data, filename=filename, course_id=form.course_id.data)
        db.session.add(video)
        db.session.commit()
        flash('Video has been uploaded!', 'success')
        return redirect(url_for('home'))
    return render_template('upload_video.html', title='Upload Video', form=form)

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploaded_files')
@login_required
def uploaded_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('uploaded_files.html', files=files)

@app.route('/stream/<filename>')
@login_required
def stream_video(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        abort(404)
    return Response(generate_video(file_path), mimetype='video/mp4')

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('course_detail.html', title=course.name, course=course)

# Video streaming
def generate_video(filename):
    with open(filename, 'rb') as video:
        while True:
            data = video.read(1024)
            if not data:
                break
            yield data

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/lesson')
@login_required
def lesson():
    return render_template('lesson.html', title='Lesson')

if __name__ == '__main__':
    # Ensure the database file is removed to recreate it with the updated schema
    if os.path.exists('site.db'):
        os.remove('site.db')
    with app.app_context():
        db.create_all()
    app.run(debug=True)
