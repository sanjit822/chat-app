from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, emit
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ========== DATABASE MODELS ==========

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    avatar = db.Column(db.String(10), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    avatar = db.Column(db.String(10), nullable=False)
    text = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(200), nullable=True)
    filename = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ========== ROUTES ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    room = request.form['room']
    username = request.form['username']
    avatar = request.form['avatar']

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(filepath)

    file_url = f"/{filepath}"

    message = Message(room=room, username=username, avatar=avatar,
                      file_url=file_url, filename=filename)
    db.session.add(message)
    db.session.commit()

    socketio.emit('file_shared', {
        'username': username,
        'avatar': avatar,
        'file_url': file_url,
        'filename': filename,
        'room': room
    }, to=room)

    return '', 204

@app.route('/messages/<room>')
def get_messages(room):
    msgs = Message.query.filter_by(room=room).order_by(Message.timestamp).all()
    result = []
    for msg in msgs:
        result.append({
            'username': msg.username,
            'avatar': msg.avatar,
            'text': msg.text,
            'file_url': msg.file_url,
            'filename': msg.filename,
            'timestamp': msg.timestamp.strftime("%H:%M")
        })
    return jsonify(result)

# ========== SOCKET.IO EVENTS ==========

@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data['username']
    avatar = data['avatar']
    join_room(room)
    emit('user_joined', {'username': username, 'avatar': avatar}, to=room)

@socketio.on('message')
def handle_message(data):
    msg = Message(
        room=data['room'],
        username=data['username'],
        avatar=data['avatar'],
        text=data['text']
    )
    db.session.add(msg)
    db.session.commit()
    emit('message', {
        'username': data['username'],
        'avatar': data['avatar'],
        'text': data['text'],
        'room': data['room']
    }, to=data['room'])

# ========== MAIN ENTRY ==========

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
