from flask import Flask, request, render_template_string, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
import uuid

app = Flask(__name__)
app.secret_key = 'b3e2f8a1c2d6432d874a8c57df4383f73a0e5b5a2c62dbf0a5f8b4c87c22c948'
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mssql+pyodbc://serveradmin:%4012Komeel200@server789.database.windows.net/komeel_database'
    '?driver=ODBC+Driver+17+for+SQL+Server'
    '&Encrypt=yes'
    '&TrustServerCertificate=yes'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

AZURE_CONNECTION_STRING = (
    'DefaultEndpointsProtocol=https;'
    'AccountName=komeel789;'
    'AccountKey=RXb3hEwKyfPrMcyBCssFgPh4/hqb150sBg7R29/6F80SCibSFq4reeo+DwzrOOkB5uwz96UVZkfN+ASt+HmYPA==;'
    'EndpointSuffix=core.windows.net'
)
AZURE_CONTAINER_NAME = 'picture'

db = SQLAlchemy(app)
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
try:
    blob_service_client.create_container(AZURE_CONTAINER_NAME)
except Exception:
    pass

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(512), nullable=False)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(256), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    people_present = db.Column(db.String(256), nullable=True)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    file_path = db.Column(db.String(512), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='media')
    ratings = db.relationship('Rating', backref='media')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'media_id', name='unique_user_media_rating'),)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>My Video Hub</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: 'Roboto', sans-serif;
                    background-color: #121212;
                    color: #e0e0e0;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }
                .welcome-card {
                    background-color: #1e1e1e;
                    padding: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                    text-align: center;
                    max-width: 400px;
                    width: 90%;
                    transition: transform 0.3s ease;
                }
                .welcome-card:hover {
                    transform: translateY(-5px);
                }
                h1 {
                    font-size: 2rem;
                    margin-bottom: 1.5rem;
                    color: #ffffff;
                }
                .nav-links a {
                    color: #03DAC6;
                    font-size: 1.1rem;
                    margin: 0 1rem;
                    text-decoration: none;
                    transition: color 0.3s ease;
                }
                .nav-links a:hover {
                    color: #26A69A;
                }
            </style>
        </head>
        <body>
            <div class="welcome-card">
                <h1>My Video Hub</h1>
                <div class="nav-links">
                    <a href="{{ url_for('login') }}">Login</a>
                    <a href="{{ url_for('register') }}">Register</a>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, role=role, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created!', 'success')
        return redirect(url_for('login'))
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Register - My Video Hub</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: 'Roboto', sans-serif;
                    background-color: #121212;
                    color: #e0e0e0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .form-card {
                    background-color: #1e1e1e;
                    padding: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                    width: 90%;
                    max-width: 400px;
                    transition: transform 0.3s ease;
                }
                .form-card:hover {
                    transform: translateY(-5px);
                }
                h1 {
                    font-size: 1.8rem;
                    margin-bottom: 1.5rem;
                    text-align: center;
                    color: #ffffff;
                }
                input, select, button {
                    width: 100%;
                    padding: 0.8rem;
                    margin-bottom: 1rem;
                    border: 1px solid #424242;
                    border-radius: 8px;
                    background-color: #2a2a2a;
                    color: #e0e0e0;
                    font-size: 1rem;
                    box-sizing: border-box;
                }
                input:focus, select:focus {
                    outline: none;
                    border-color: #03DAC6;
                }
                button {
                    background-color: #03DAC6;
                    border: none;
                    cursor: pointer;
                    font-weight: bold;
                    transition: background-color 0.3s ease;
                }
                button:hover {
                    background-color: #26A69A;
                }
            </style>
        </head>
        <body>
            <div class="form-card">
                <h1>Register</h1>
                <form method="POST">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="email" name="email" placeholder="Email" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <select name="role" required>
                        <option value="creator">Creator</option>
                        <option value="consumer">Consumer</option>
                    </select>
                    <button type="submit">Register</button>
                </form>
            </div>
        </body>
        </html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed.', 'danger')
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login - My Video Hub</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: 'Roboto', sans-serif;
                    background-color: #121212;
                    color: #e0e0e0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .form-card {
                    background-color: #1e1e1e;
                    padding: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                    width: 90%;
                    max-width: 400px;
                    transition: transform 0.3s ease;
                }
                .form-card:hover {
                    transform: translateY(-5px);
                }
                h1 {
                    font-size: 1.8rem;
                    margin-bottom: 1.5rem;
                    text-align: center;
                    color: #ffffff;
                }
                input, button {
                    width: 100%;
                    padding: 0.8rem;
                    margin-bottom: 1rem;
                    border: 1px solid #424242;
                    border-radius: 8px;
                    background-color: #2a2a2a;
                    color: #e0e0e0;
                    font-size: 1rem;
                    box-sizing: border-box;
                }
                input:focus {
                    outline: none;
                    border-color: #03DAC6;
                }
                button {
                    background-color: #03DAC6;
                    border: none;
                    cursor: pointer;
                    font-weight: bold;
                    transition: background-color 0.3s ease;
                }
                button:hover {
                    background-color: #26A69A;
                }
            </style>
        </head>
        <body>
            <div class="form-card">
                <h1>Login</h1>
                <form method="POST">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
    ''')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_query = request.form.get('search_query', '')
    media = Media.query.filter(Media.title.contains(search_query)).options(
        joinedload(Media.comments),
        joinedload(Media.ratings)
    ).all()

    if session['role'] == 'creator':
        return render_template_string('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Creator Dashboard - My Video Hub</title>
                <style>
                    body {
                        margin: 0;
                        padding: 2rem;
                        font-family: 'Roboto', sans-serif;
                        background-color: #121212;
                        color: #e0e0e0;
                        min-height: 100vh;
                    }
                    .dashboard {
                        max-width: 800px;
                        margin: 0 auto;
                    }
                    .card {
                        background-color: #1e1e1e;
                        padding: 2rem;
                        border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                        margin-bottom: 2rem;
                        transition: transform 0.3s ease;
                    }
                    .card:hover {
                        transform: translateY(-5px);
                    }
                    h1 {
                        font-size: 2rem;
                        margin-bottom: 1.5rem;
                        color: #ffffff;
                        text-align: center;
                    }
                    input, select, button {
                        width: 100%;
                        padding: 0.8rem;
                        margin-bottom: 1rem;
                        border: 1px solid #424242;
                        border-radius: 8px;
                        background-color: #2a2a2a;
                        color: #e0e0e0;
                        font-size: 1rem;
                        box-sizing: border-box;
                    }
                    input:focus, select:focus {
                        outline: none;
                        border-color: #03DAC6;
                    }
                    button {
                        background-color: #03DAC6;
                        border: none;
                        cursor: pointer;
                        font-weight: bold;
                        transition: background-color 0.3s ease;
                    }
                    button:hover {
                        background-color: #26A69A;
                    }
                    a.logout {
                        color: #CF6679;
                        text-decoration: none;
                        display: block;
                        text-align: center;
                        margin-top: 1rem;
                        transition: color 0.3s ease;
                    }
                    a.logout:hover {
                        color: #EF5350;
                    }
                </style>
            </head>
            <body>
                <div class="dashboard">
                    <div class="card">
                        <h1>Creator Dashboard</h1>
                        <form method="POST" action="{{ url_for('upload') }}" enctype="multipart/form-data">
                            <input type="text" name="title" placeholder="Title" required>
                            <input type="text" name="caption" placeholder="Caption">
                            <input type="text" name="location" placeholder="Location">
                            <input type="text" name="people_present" placeholder="People Present">
                            <input type="file" name="file" required>
                            <select name="media_type" required>
                                <option value="video">Video</option>
                                <option value="picture">Picture</option>
                            </select>
                            <button type="submit">Upload Media</button>
                        </form>
                        <a class="logout" href="{{ url_for('logout') }}">Logout</a>
                    </div>
                </div>
            </body>
            </html>
        ''')

    else:
        return render_template_string('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Consumer Dashboard - My Video Hub</title>
                <style>
                    body {
                        margin: 0;
                        padding: 2rem;
                        font-family: 'Roboto', sans-serif;
                        background-color: #121212;
                        color: #e0e0e0;
                        min-height: 100vh;
                    }
                    .dashboard {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                    .card {
                        background-color: #1e1e1e;
                        padding: 1.5rem;
                        border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                        margin-bottom: 2rem;
                        transition: transform 0.3s ease;
                    }
                    .card:hover {
                        transform: translateY(-5px);
                    }
                    h1 {
                        font-size: 2rem;
                        margin-bottom: 1.5rem;
                        color: #ffffff;
                        text-align: center;
                    }
                    h2 {
                        font-size: 1.5rem;
                        margin-bottom: 1rem;
                        color: #ffffff;
                    }
                    h4 {
                        font-size: 1.2rem;
                        margin: 1rem 0;
                        color: #B0BEC5;
                    }
                    input, button {
                        width: 100%;
                        padding: 0.8rem;
                        margin-bottom: 1rem;
                        border: 1px solid #424242;
                        border-radius: 8px;
                        background-color: #2a2a2a;
                        color: #e0e0e0;
                        font-size: 1rem;
                        box-sizing: border-box;
                    }
                    input:focus {
                        outline: none;
                        border-color: #03DAC6;
                    }
                    button {
                        background-color: #03DAC6;
                        border: none;
                        cursor: pointer;
                        font-weight: bold;
                        transition: background-color 0.3s ease;
                    }
                    button:hover {
                        background-color: #26A69A;
                    }
                    video, img {
                        max-width: 100%;
                        height: auto;
                        border-radius: 8px;
                        margin: 1rem 0;
                    }
                    ul {
                        list-style-type: none;
                        padding: 0;
                        margin: 0;
                    }
                    li {
                        padding: 0.5rem 0;
                        border-bottom: 1px solid #424242;
                    }
                    li:last-child {
                        border-bottom: none;
                    }
                    .search-form {
                        margin-bottom: 2rem;
                    }
                    a.logout {
                        color: #CF6679;
                        text-decoration: none;
                        display: block;
                        text-align: center;
                        margin-top: 1rem;
                        transition: color 0.3s ease;
                    }
                    a.logout:hover {
                        color: #EF5350;
                    }
                    hr {
                        border: 0;
                        border-top: 1px solid #424242;
                        margin: 1rem 0;
                    }
                    p.no-results {
                        text-align: center;
                        color: #B0BEC5;
                    }
                </style>
            </head>
            <body>
                <div class="dashboard">
                    <h1>Consumer Dashboard</h1>
                    <div class="card search-form">
                        <form method="POST" action="{{ url_for('dashboard') }}">
                            <input type="text" name="search_query" placeholder="Search by Title" value="{{ request.form.get('search_query', '') }}">
                            <button type="submit">Search</button>
                        </form>
                    </div>

                    {% if not media %}
                        <p class="no-results">No results found.</p>
                    {% endif %}

                    {% for item in media %}
                        <div class="card">
                            <h2>{{ item.title | e }}</h2>
                            <p>{{ item.caption | e }}</p>
                            {% if item.media_type == 'video' %}
                                <video width="100%" controls>
                                    <source src="{{ item.file_path | e }}" type="video/mp4">
                                    Your browser does not support video playback.
                                </video>
                            {% else %}
                                <img src="{{ item.file_path | e }}" alt="Picture">
                            {% endif %}
                            <h4>Comments:</h4>
                            <ul>
                                {% for comment in item.comments %}
                                    <li>{{ comment.text | e }}</li>
                                {% endfor %}
                                {% if not item.comments %}
                                    <li>No comments yet.</li>
                                {% endif %}
                            </ul>
                            <form method="POST" action="{{ url_for('comment') }}">
                                <input type="hidden" name="media_id" value="{{ item.id }}">
                                <input type="text" name="text" placeholder="Comment" required>
                                <button type="submit">Comment</button>
                            </form>
                            <h4>Ratings:</h4>
                            <ul>
                                {% for rating in item.ratings %}
                                    <li>{{ rating.value | e }}/5</li>
                                {% endfor %}
                                {% if not item.ratings %}
                                    <li>No ratings yet.</li>
                                {% endif %}
                            </ul>
                            <form method="POST" action="{{ url_for('rate') }}">
                                <input type="hidden" name="media_id" value="{{ item.id }}">
                                <input type="number" name="value" min="1" max="5" required>
                                <button type="submit">Rate</button>
                            </form>
                            <hr>
                        </div>
                    {% endfor %}

                    <a class="logout" href="{{ url_for('logout') }}">Logout</a>
                </div>
            </body>
            </html>
        ''', media=media)

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session or session['role'] != 'creator':
        return redirect(url_for('login'))
    title = request.form['title']
    caption = request.form['caption']
    location = request.form['location']
    people_present = request.form['people_present']
    file = request.files['file']
    media_type = request.form['media_type']
    if file:
        filename = file.filename
        blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=filename)
        blob_client.upload_blob(file, overwrite=True, content_settings=ContentSettings(
            content_type='video/mp4' if media_type == 'video' else 'image/jpeg'))
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{filename}"
        media = Media(
            title=title,
            caption=caption,
            location=location,
            people_present=people_present,
            file_path=blob_url,
            media_type=media_type if media_type in ['video', 'picture'] else 'picture',
            creator_id=session['user_id']
        )
        db.session.add(media)
        db.session.commit()
        flash('Media uploaded successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/comment', methods=['POST'])
def comment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    comment = Comment(
        text=request.form['text'],
        user_id=session['user_id'],
        media_id=request.form['media_id']
    )
    db.session.add(comment)
    db.session.commit()
    flash('Comment added!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/rate', methods=['POST'])
def rate():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    media_id = request.form.get('media_id')
    if not media_id:
        flash('Media ID is required to rate!', 'danger')
        return redirect(url_for('dashboard'))
    try:
        media_id = int(media_id)
    except ValueError:
        flash('Invalid Media ID!', 'danger')
        return redirect(url_for('dashboard'))
    media = Media.query.get(media_id)
    if not media:
        flash('Invalid media item!', 'danger')
        return redirect(url_for('dashboard'))
    existing_rating = Rating.query.filter_by(user_id=session['user_id'], media_id=media_id).first()
    if existing_rating:
        flash('You have already rated this media!', 'warning')
        return redirect(url_for('dashboard'))
    rating = Rating(
        value=int(request.form['value']),
        user_id=session['user_id'],
        media_id=media_id
    )
    db.session.add(rating)
    try:
        db.session.commit()
        flash('Media rated!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Error submitting rating.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()