import sqlite3
import os
import requests
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
from chat_engine import chat_engine

app = Flask(__name__)
app.secret_key = 'xssbook_vulnerable_secret_key_123'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('xssbook.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            bio TEXT DEFAULT '',
            signature TEXT DEFAULT '',
            avatar TEXT DEFAULT '',
            cover_photo TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Posts table (cached posts from APIs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT DEFAULT '',
            video_url TEXT DEFAULT '',
            is_cached BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            related_user_id INTEGER,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (related_user_id) REFERENCES users (id)
        )
    ''')
    
    # Comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Likes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(post_id, user_id)
        )
    ''')
    
    # Friend requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friend_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id),
            UNIQUE(sender_id, receiver_id)
        )
    ''')
    
    # Friends table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user1_id) REFERENCES users (id),
            FOREIGN KEY (user2_id) REFERENCES users (id),
            UNIQUE(user1_id, user2_id)
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Sample data population
def populate_sample_data():
    conn = sqlite3.connect('xssbook.db')
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    try:
        # Fetch dummy users from RandomUser API
        response = requests.get('https://randomuser.me/api/?results=20&nat=us,gb,ca,au', timeout=10)
        users_data = response.json()['results']
        
        dummy_users = []
        
        # Create dummy users with vulnerabilities
        for i, user_data in enumerate(users_data):
            username = f"{user_data['login']['username']}{random.randint(1, 999)}"
            name = f"{user_data['name']['first']} {user_data['name']['last']}"
            email = user_data['email']
            avatar = user_data['picture']['large']
            cover_photo = f"https://picsum.photos/1200/400?random={i + 100}"
            
            # Add normal, safe bios for dummy users
            safe_bios = [
                f"Hello! I'm {name}, nice to meet you!",
                f"Welcome to my profile! Love connecting with new people.",
                f"Tech enthusiast and passionate developer",
                f"Love coding and learning new technologies!",
                f"Check out my website for my latest projects!",
                f"Coffee lover ☕ Always ready for a chat!",
                f"Adventure seeker 🌍",
                f"Photographer 📸",
                f"Foodie 🍕",
                f"Music lover 🎵",
                f"Travel enthusiast ✈️",
                f"Fitness lover 💪",
                f"Book worm 📚",
                f"Gaming enthusiast 🎮",
                f"Nature lover 🌲"
            ]
            
            bio = random.choice(safe_bios)
            
            # Safe signatures for dummy users
            safe_signatures = [
                "Moving forward with passion!",
                "Always learning something new",
                "Best regards and happy coding!",
                "Stay connected and keep growing!",
                "Happy coding and best wishes!",
                "Peace out! ✌️",
                "Stay awesome! 🌟",
                "Keep learning! 📚",
                "Dream big! 💫",
                "Spread kindness 💖",
                "Live, laugh, love! 😊",
                "Carpe Diem! ⭐",
                "Be yourself! 🌈",
                "Never give up! 💪",
                "Enjoy the journey! 🚀"
            ]
            
            signature = random.choice(safe_signatures)
            
            password_hash = generate_password_hash('password123')
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, name, bio, signature, avatar, cover_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, name, bio, signature, avatar, cover_photo))
            
            dummy_users.append({
                'id': cursor.lastrowid,
                'username': username,
                'name': name
            })
        
        # Create interesting posts with safe content for dummy users
        safe_posts = [
            {
                'content': "Just learned about web security best practices!",
                'image_url': "https://picsum.photos/800/600?random=1"
            },
            {
                'content': "Check out this cool website I found today!",
                'image_url': ""
            },
            {
                'content': "Beautiful sunset today! Perfect weather for photography.",
                'image_url': "https://picsum.photos/800/600?random=2"
            },
            {
                'content': "Love this new framework I'm learning. Very intuitive!",
                'image_url': ""
            },
            {
                'content': "Coffee break time! ☕ Perfect way to recharge.",
                'image_url': "https://picsum.photos/800/600?random=3"
            },
            {
                'content': "Working on a new project with some exciting features!",
                'image_url': "https://picsum.photos/800/600?random=4"
            },
            {
                'content': "Amazing concert last night! The music was absolutely fantastic",
                'image_url': "https://picsum.photos/800/600?random=5"
            },
            {
                'content': "Learning React and loving every minute of it! Such a powerful library.",
                'image_url': ""
            },
            {
                'content': "Beach day! 🏖️ Perfect weather for swimming and relaxing.",
                'image_url': "https://picsum.photos/800/600?random=6"
            },
            {
                'content': "Just finished reading an amazing book! 📚 Highly recommend it to everyone.",
                'image_url': "https://picsum.photos/800/600?random=7"
            },
            {
                'content': "Cooking experiment today! Trying out a new recipe I found online.",
                'image_url': "https://picsum.photos/800/600?random=8"
            },
            {
                'content': "Mountain hiking adventure! 🏔️ The view from the top was breathtaking.",
                'image_url': "https://picsum.photos/800/600?random=9"
            },
            {
                'content': "Pet update: My cat learned a new trick today! So proud of her.",
                'image_url': "https://picsum.photos/800/600?random=10"
            },
            {
                'content': "Game night with friends! 🎮 We played until 3 AM and it was worth it.",
                'image_url': "https://picsum.photos/800/600?random=11"
            },
            {
                'content': "Travel plans are coming together! Europe here I come!",
                'image_url': "https://picsum.photos/800/600?random=12"
            },
            {
                'content': "Art gallery visit today! 🎨 So much inspiration and creativity in one place.",
                'image_url': "https://picsum.photos/800/600?random=13"
            },
            {
                'content': "Fitness journey update: Making great progress this month!",
                'image_url': ""
            },
            {
                'content': "Garden update! 🌱 My tomatoes are finally ready to harvest.",
                'image_url': "https://picsum.photos/800/600?random=14"
            },
            {
                'content': "Movie night: Watched a fantastic film! Highly recommend it.",
                'image_url': ""
            },
            {
                'content': "Weekend farmers market! 🥕 Fresh vegetables and friendly vendors.",
                'image_url': "https://picsum.photos/800/600?random=15"
            }
        ]
        
        # Create posts for dummy users
        for i, post in enumerate(safe_posts):
            if i < len(dummy_users):
                user = dummy_users[i]
                cursor.execute('''
                    INSERT INTO posts (user_id, content, image_url, is_cached)
                    VALUES (?, ?, ?, 1)
                ''', (user['id'], post['content'], post['image_url']))
        
        # Create some friend relationships between dummy users (auto-friendship)
        for i in range(len(dummy_users)):
            for j in range(i + 1, min(i + 4, len(dummy_users))):
                user1_id = dummy_users[i]['id']
                user2_id = dummy_users[j]['id']
                
                cursor.execute('''
                    INSERT OR IGNORE INTO friends (user1_id, user2_id)
                    VALUES (?, ?)
                ''', (min(user1_id, user2_id), max(user1_id, user2_id)))
        
        # Add safe comments for dummy users
        safe_comments = [
            "Great post! Thanks for sharing.",
            "Love it! Very inspiring content.",
            "Awesome content! Keep it up.",
            "Thanks for sharing this! Really helpful.",
            "Amazing! Looking forward to more posts like this.",
            "Nice work! 👍",
            "Incredible post!",
            "Keep it up!",
            "So inspiring!",
            "Well said!"
        ]
        
        cursor.execute('SELECT id FROM posts')
        post_ids = [row[0] for row in cursor.fetchall()]
        
        for post_id in post_ids:
            # Add 1-3 comments per post
            for _ in range(random.randint(1, 3)):
                if dummy_users:
                    commenter = random.choice(dummy_users)
                    comment_content = random.choice(safe_comments)
                    
                    cursor.execute('''
                        INSERT INTO comments (post_id, user_id, content)
                        VALUES (?, ?, ?)
                    ''', (post_id, commenter['id'], comment_content))
        
        conn.commit()
        print(f"Created {len(dummy_users)} dummy users with posts and friendships")
        
    except Exception as e:
        print(f"Error creating dummy data: {e}")
        # Create basic dummy users if API fails
        basic_users = [
            ('alice_wonder', 'alice@example.com', 'Alice Wonderland', 'Curious explorer and adventure enthusiast'),
            ('bob_builder', 'bob@example.com', 'Bob Builder', 'Can we fix it? Yes we can! Construction expert.'),
            ('charlie_brown', 'charlie@example.com', 'Charlie Brown', 'Good grief! Baseball and comic enthusiast.')
        ]
        
        for username, email, name, bio in basic_users:
            password_hash = generate_password_hash('password123')
            avatar = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=1877f2&color=fff&size=200"
            cover_photo = f"https://picsum.photos/1200/400?random={hash(username) % 100}"
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, name, bio, avatar, cover_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, name, bio, avatar, cover_photo))

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('xssbook.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def get_posts_with_users():
    conn = get_db_connection()
    posts = conn.execute('''
        SELECT p.*, u.name, u.username, u.avatar,
               (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
               (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    conn.close()
    return posts

def get_friendship_status(user1_id, user2_id):
    """Get friendship status between two users"""
    conn = get_db_connection()
    
    # Check if they are friends
    friendship = conn.execute('''
        SELECT id FROM friends 
        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    ''', (user1_id, user2_id, user2_id, user1_id)).fetchone()
    
    if friendship:
        conn.close()
        return 'friends'
    
    # Check if there's a pending request from current user to target user
    outgoing_request = conn.execute('''
        SELECT id FROM friend_requests 
        WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
    ''', (user1_id, user2_id)).fetchone()
    
    if outgoing_request:
        conn.close()
        return 'request_sent'
    
    # Check if there's a pending request from target user to current user
    incoming_request = conn.execute('''
        SELECT id FROM friend_requests 
        WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
    ''', (user2_id, user1_id)).fetchone()
    
    if incoming_request:
        conn.close()
        return 'request_received'
    
    conn.close()
    return 'none'

# VULNERABILITY: Flawed sanitization functions
def sanitize_basic(content):
    """VULNERABLE: Only removes <script> tags - easily bypassed"""
    if content is None:
        return ""
    return content.replace('<script>', '').replace('</script>', '')

def sanitize_partial(content):
    """VULNERABLE: Only escapes < and > - misses attributes and other tags"""
    if content is None:
        return ""
    return content.replace('<', '&lt;').replace('>', '&gt;')

def sanitize_blacklist(content):
    """VULNERABLE: Blacklist approach - easily bypassed with case variations"""
    if content is None:
        return ""
    blacklisted = ['<script>', '</script>', '<iframe>', '</iframe>']
    result = content
    for item in blacklisted:
        result = result.replace(item, '')
    return result

# Routes
@app.route('/')
def index():
    posts = get_posts_with_users()
    current_user = None
    if 'user_id' in session:
        current_user = get_user_by_id(session['user_id'])
    return render_template('index.html', posts=posts, current_user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        
        if not all([username, email, password, name]):
            flash('All fields are required!')
            return render_template('register.html')
        
        conn = get_db_connection()
        
        # Check if user exists
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()
        
        if existing_user:
            flash('Username or email already exists!')
            conn.close()
            return render_template('register.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        cursor = conn.execute('''
            INSERT INTO users (username, email, password_hash, name)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, name))
        
        new_user_id = cursor.lastrowid
        
        # Create some welcome friend requests from existing users
        existing_users = conn.execute('SELECT id FROM users WHERE id != ? LIMIT 3', (new_user_id,)).fetchall()
        for user in existing_users:
            try:
                conn.execute('''
                    INSERT INTO friend_requests (sender_id, receiver_id, status)
                    VALUES (?, ?, 'pending')
                ''', (user['id'], new_user_id))
            except:
                pass  # Ignore duplicates
        
        conn.commit()
        conn.close()
        
        flash('Registration successful! You have some friend requests waiting.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            
            # Check if user needs to complete profile setup
            if not user['avatar'] and not user['bio']:
                return redirect(url_for('setup_profile'))
            
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile/<username>')
def profile(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if not user:
        flash('User not found!')
        return redirect(url_for('index'))
    
    posts = conn.execute('''
        SELECT p.*, u.name, u.username, u.avatar,
               (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
               (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
        ORDER BY p.created_at DESC
    ''', (user['id'],)).fetchall()
    
    current_user = None
    is_own_profile = False
    friendship_status = 'none'
    if 'user_id' in session:
        current_user = get_user_by_id(session['user_id'])
        is_own_profile = (session['user_id'] == user['id'])
        if not is_own_profile:
            friendship_status = get_friendship_status(session['user_id'], user['id'])
    
    conn.close()
    return render_template('profile.html', user=user, posts=posts, current_user=current_user, 
                         is_own_profile=is_own_profile, friendship_status=friendship_status)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        bio = request.form['bio']
        signature = request.form['signature']  # VULNERABLE: No sanitization
        avatar_url = request.form.get('avatar_url', '')
        
        # Handle file upload for avatar
        if 'avatar_file' in request.files:
            file = request.files['avatar_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Add timestamp to avoid filename conflicts
                filename = f"{int(datetime.now().timestamp())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    avatar_url = url_for('uploaded_file', filename=filename)
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE users SET name = ?, bio = ?, signature = ?, avatar = ?
            WHERE id = ?
        ''', (name, bio, signature, avatar_url, session['user_id']))
        conn.commit()
        conn.close()
        
        session['name'] = name
        flash('Profile updated successfully!')
        return redirect(url_for('profile', username=session['username']))
    
    user = get_user_by_id(session['user_id'])
    return render_template('edit_profile.html', user=user)

@app.route('/setup_profile')
def setup_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    # Check if user needs profile setup (no avatar or bio)
    if user['avatar'] or user['bio']:
        return redirect(url_for('profile', username=user['username']))
    
    return render_template('setup_profile.html', user=user)

@app.route('/complete_profile', methods=['POST'])
def complete_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    bio = request.form.get('bio', '')
    avatar_url = request.form.get('avatar_url', '')
    
    # Handle file upload for avatar
    if 'avatar_file' in request.files:
        file = request.files['avatar_file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                avatar_url = url_for('uploaded_file', filename=filename)
    
    # If no custom avatar, get a random one
    if not avatar_url:
        try:
            random_user_response = requests.get('https://randomuser.me/api/', timeout=5)
            random_user_data = random_user_response.json()
            avatar_url = random_user_data['results'][0]['picture']['large']
        except:
            avatar_url = f"https://via.placeholder.com/150x150/1877f2/ffffff?text={session['name'][0]}"
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE users SET bio = ?, avatar = ?
        WHERE id = ?
    ''', (bio, avatar_url, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Profile setup completed!')
    return redirect(url_for('profile', username=session['username']))

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form['content']
    image_url = request.form.get('image_url', '')
    video_url = request.form.get('video_url', '')
    
    # Handle file upload
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)  # Secure filename but content is still vulnerable
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_url = url_for('uploaded_file', filename=filename)
            elif file.filename.lower().endswith(('.mp4', '.avi', '.mov')):
                video_url = url_for('uploaded_file', filename=filename)
    
    # VULNERABLE: Minimal sanitization on content
    sanitized_content = sanitize_basic(content)
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO posts (user_id, content, image_url, video_url)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], sanitized_content, image_url, video_url))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/add_comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    post_id = request.form['post_id']
    content = request.form['content']
    
    # VULNERABLE: No sanitization on comments
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO comments (post_id, user_id, content)
        VALUES (?, ?, ?)
    ''', (post_id, session['user_id'], content))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = []
    
    if query:
        conn = get_db_connection()
        # VULNERABLE: Direct query injection into template without sanitization
        results = conn.execute('''
            SELECT p.*, u.name, u.username, u.avatar
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.content LIKE ? OR u.name LIKE ?
            ORDER BY p.created_at DESC
        ''', (f'%{query}%', f'%{query}%')).fetchall()
        conn.close()
    
    current_user = None
    if 'user_id' in session:
        current_user = get_user_by_id(session['user_id'])
    
    return render_template('search.html', query=query, results=results, current_user=current_user)

@app.route('/personalize')
def personalize():
    """VULNERABLE: DOM-based XSS through URL parameter"""
    current_user = None
    if 'user_id' in session:
        current_user = get_user_by_id(session['user_id'])
    return render_template('personalize.html', current_user=current_user)

@app.route('/get_comments/<int:post_id>')
def get_comments(post_id):
    conn = get_db_connection()
    comments = conn.execute('''
        SELECT c.*, u.name, u.username, u.avatar
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    ''', (post_id,)).fetchall()
    conn.close()
    
    return jsonify([{
        'id': comment['id'],
        'content': comment['content'],  # VULNERABLE: Raw content returned
        'name': comment['name'],
        'username': comment['username'],
        'avatar': comment['avatar'],
        'created_at': comment['created_at']
    } for comment in comments])

@app.route('/like_post', methods=['POST'])
def like_post():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    post_id = request.json.get('post_id')
    
    conn = get_db_connection()
    
    # Check if already liked
    existing_like = conn.execute(
        'SELECT id FROM likes WHERE post_id = ? AND user_id = ?',
        (post_id, session['user_id'])
    ).fetchone()
    
    if existing_like:
        # Unlike
        conn.execute('DELETE FROM likes WHERE post_id = ? AND user_id = ?',
                    (post_id, session['user_id']))
        liked = False
    else:
        # Like
        conn.execute('INSERT INTO likes (post_id, user_id) VALUES (?, ?)',
                    (post_id, session['user_id']))
        liked = True
    
    # Get updated like count
    like_count = conn.execute(
        'SELECT COUNT(*) FROM likes WHERE post_id = ?',
        (post_id,)
    ).fetchone()[0]
    
    conn.commit()
    conn.close()
    
    return jsonify({'liked': liked, 'like_count': like_count})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/send_friend_request', methods=['POST'])
def send_friend_request():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    receiver_id = request.json.get('receiver_id')
    sender_id = session['user_id']
    
    if sender_id == receiver_id:
        return jsonify({'error': 'Cannot send friend request to yourself'}), 400
    
    conn = get_db_connection()
    
    # Check current friendship status
    friendship_status = get_friendship_status(sender_id, receiver_id)
    
    if friendship_status == 'friends':
        conn.close()
        return jsonify({'error': 'Already friends'}), 400
    
    if friendship_status == 'request_sent':
        conn.close()
        return jsonify({'error': 'Friend request already sent'}), 400
    
    if friendship_status == 'request_received':
        conn.close()
        return jsonify({'error': 'This user has already sent you a friend request. Check your friend requests.'}), 400
    
    # Get receiver info to check if they're a dummy user
    receiver = conn.execute('SELECT username, name FROM users WHERE id = ?', (receiver_id,)).fetchone()
    sender = conn.execute('SELECT username, name FROM users WHERE id = ?', (sender_id,)).fetchone()
    
    if not receiver:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    # Create friend request
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO friend_requests (sender_id, receiver_id, status)
        VALUES (?, ?, 'pending')
    ''', (sender_id, receiver_id))
    request_id = cursor.lastrowid
    
    # Check if receiver is a dummy user (check password)
    receiver_data = conn.execute('SELECT password_hash FROM users WHERE id = ?', (receiver_id,)).fetchone()
    is_dummy = False
    if receiver_data:
        is_dummy = check_password_hash(receiver_data['password_hash'], 'password123')
    
    if is_dummy:
        # Auto-accept from dummy users
        cursor.execute('''
            UPDATE friend_requests SET status = 'accepted' WHERE id = ?
        ''', (request_id,))
        
        # Add to friends table
        cursor.execute('''
            INSERT INTO friends (user1_id, user2_id)
            VALUES (?, ?)
        ''', (min(sender_id, receiver_id), max(sender_id, receiver_id)))
        
        # Create notification for sender
        cursor.execute('''
            INSERT INTO notifications (user_id, type, message, related_user_id)
            VALUES (?, ?, ?, ?)
        ''', (sender_id, 'friend_accepted', f'{receiver["name"]} accepted your friend request!', receiver_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Friend request automatically accepted!', 'auto_accepted': True})
    else:
        # Create notification for receiver
        cursor.execute('''
            INSERT INTO notifications (user_id, type, message, related_user_id)
            VALUES (?, ?, ?, ?)
        ''', (receiver_id, 'friend_request', f'{sender["name"]} sent you a friend request!', sender_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Friend request sent'})

@app.route('/respond_friend_request', methods=['POST'])
def respond_friend_request():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    sender_id = request.json.get('sender_id')
    action = request.json.get('action')  # 'accept' or 'decline'
    receiver_id = session['user_id']
    
    if action not in ['accept', 'decline']:
        return jsonify({'error': 'Invalid action'}), 400
    
    conn = get_db_connection()
    
    # Check if friend request exists
    friend_request = conn.execute('''
        SELECT id FROM friend_requests 
        WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
    ''', (sender_id, receiver_id)).fetchone()
    
    if not friend_request:
        conn.close()
        return jsonify({'error': 'Friend request not found'}), 404
    
    cursor = conn.cursor()
    
    if action == 'accept':
        # Update request status
        cursor.execute('''
            UPDATE friend_requests SET status = 'accepted' WHERE id = ?
        ''', (friend_request['id'],))
        
        # Add to friends table
        cursor.execute('''
            INSERT INTO friends (user1_id, user2_id)
            VALUES (?, ?)
        ''', (min(sender_id, receiver_id), max(sender_id, receiver_id)))
        
        # Get names for notifications
        sender = conn.execute('SELECT name FROM users WHERE id = ?', (sender_id,)).fetchone()
        receiver = conn.execute('SELECT name FROM users WHERE id = ?', (receiver_id,)).fetchone()
        
        # Create notification for sender
        cursor.execute('''
            INSERT INTO notifications (user_id, type, message, related_user_id)
            VALUES (?, ?, ?, ?)
        ''', (sender_id, 'friend_accepted', f'{receiver["name"]} accepted your friend request!', receiver_id))
        
        message = 'Friend request accepted!'
    else:
        # Update request status to declined
        cursor.execute('''
            UPDATE friend_requests SET status = 'declined' WHERE id = ?
        ''', (friend_request['id'],))
        
        message = 'Friend request declined'
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': message})

@app.route('/get_friend_requests')
def get_friend_requests():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    
    # Get pending friend requests
    requests_data = conn.execute('''
        SELECT fr.id, fr.sender_id, u.name, u.username, u.avatar, fr.created_at
        FROM friend_requests fr
        JOIN users u ON fr.sender_id = u.id
        WHERE fr.receiver_id = ? AND fr.status = 'pending'
        ORDER BY fr.created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return jsonify([{
        'id': req['id'],
        'sender_id': req['sender_id'],
        'name': req['name'],
        'username': req['username'],
        'avatar': req['avatar'],
        'created_at': req['created_at']
    } for req in requests_data])

@app.route('/get_friends')
def get_friends():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    
    # Get friends list
    friends_data = conn.execute('''
        SELECT u.id, u.name, u.username, u.avatar, u.bio
        FROM friends f
        JOIN users u ON (f.user1_id = u.id OR f.user2_id = u.id)
        WHERE (f.user1_id = ? OR f.user2_id = ?) AND u.id != ?
        ORDER BY u.name
    ''', (session['user_id'], session['user_id'], session['user_id'])).fetchall()
    
    conn.close()
    
    return jsonify([{
        'id': friend['id'],
        'name': friend['name'],
        'username': friend['username'],
        'avatar': friend['avatar'],
        'bio': friend['bio']
    } for friend in friends_data])

@app.route('/friends')
def friends_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_user_by_id(session['user_id'])
    return render_template('friends.html', current_user=current_user)

@app.route('/get_all_users')
def get_all_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    
    # Get users who are not friends and not the current user
    users_data = conn.execute('''
        SELECT u.id, u.name, u.username, u.avatar, u.bio
        FROM users u
        WHERE u.id != ? 
        AND u.id NOT IN (
            SELECT CASE 
                WHEN f.user1_id = ? THEN f.user2_id 
                ELSE f.user1_id 
            END
            FROM friends f
            WHERE f.user1_id = ? OR f.user2_id = ?
        )
        AND u.id NOT IN (
            SELECT fr.receiver_id
            FROM friend_requests fr
            WHERE fr.sender_id = ? AND fr.status = 'pending'
        )
        ORDER BY u.name
        LIMIT 10
    ''', (session['user_id'], session['user_id'], session['user_id'], 
          session['user_id'], session['user_id'])).fetchall()
    
    conn.close()
    
    return jsonify([{
        'id': user['id'],
        'name': user['name'],
        'username': user['username'],
        'avatar': user['avatar'],
        'bio': user['bio']
    } for user in users_data])

# Notifications route
@app.route('/get_notifications')
def get_notifications():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    notifications = conn.execute('''
        SELECT n.*, u.name as related_user_name, u.avatar as related_user_avatar
        FROM notifications n
        LEFT JOIN users u ON n.related_user_id = u.id
        WHERE n.user_id = ?
        ORDER BY n.created_at DESC
        LIMIT 10
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return jsonify([{
        'id': n['id'],
        'type': n['type'],
        'message': n['message'],
        'is_read': n['is_read'],
        'created_at': n['created_at'],
        'related_user_name': n['related_user_name'],
        'related_user_avatar': n['related_user_avatar']
    } for n in notifications])

@app.route('/mark_notification_read', methods=['POST'])
def mark_notification_read():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    notification_id = request.json.get('notification_id')
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE notifications SET is_read = 1 
        WHERE id = ? AND user_id = ?
    ''', (notification_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/update_cover_photo', methods=['POST'])
def update_cover_photo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cover_photo_url = request.form.get('cover_photo_url', '')
    
    # Handle file upload
    if 'cover_photo_file' in request.files:
        file = request.files['cover_photo_file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Add timestamp to avoid filename conflicts
            filename = f"{int(datetime.now().timestamp())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cover_photo_url = url_for('uploaded_file', filename=filename)
    
    if cover_photo_url:
        conn = get_db_connection()
        conn.execute('''
            UPDATE users SET cover_photo = ? WHERE id = ?
        ''', (cover_photo_url, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Cover photo updated successfully!')
    
    return redirect(url_for('profile', username=session['username']))

# Generate random friend requests for new users
@app.route('/generate_friend_requests')
def generate_friend_requests():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    
    # Get dummy users (those with default password)
    # Get potential dummy users and filter by password
    all_users = conn.execute('''
        SELECT id, name, username, avatar, password_hash FROM users 
        WHERE id != ?
        ORDER BY RANDOM()
    ''', (session['user_id'],)).fetchall()
    
    dummy_users = []
    for user in all_users:
        if check_password_hash(user['password_hash'], 'password123'):
            dummy_users.append(user)
            if len(dummy_users) >= 5:  # Limit to 5
                break
    
    current_user = conn.execute('SELECT name FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    cursor = conn.cursor()
    for dummy_user in dummy_users:
        # Check if request already exists
        existing = conn.execute('''
            SELECT id FROM friend_requests 
            WHERE sender_id = ? AND receiver_id = ?
        ''', (dummy_user['id'], session['user_id'])).fetchone()
        
        if not existing:
            # Create friend request from dummy user to current user
            cursor.execute('''
                INSERT INTO friend_requests (sender_id, receiver_id, status)
                VALUES (?, ?, 'pending')
            ''', (dummy_user['id'], session['user_id']))
            
            # Create notification
            cursor.execute('''
                INSERT INTO notifications (user_id, type, message, related_user_id)
                VALUES (?, ?, ?, ?)
            ''', (session['user_id'], 'friend_request', f'{dummy_user["name"]} sent you a friend request!', dummy_user['id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Friend requests generated'})

# Messaging routes with XSS vulnerabilities
@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_user_by_id(session['user_id'])
    return render_template('messages.html', current_user=current_user)

@app.route('/messages/<username>')
def chat_with_user(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    chat_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if not chat_user:
        flash('User not found!')
        return redirect(url_for('messages_page'))
    
    # Check if they are friends
    friendship_status = get_friendship_status(session['user_id'], chat_user['id'])
    if friendship_status != 'friends':
        flash('You can only message friends!')
        return redirect(url_for('messages_page'))
    
    current_user = get_user_by_id(session['user_id'])
    conn.close()
    return render_template('chat.html', current_user=current_user, chat_user=chat_user)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    receiver_id = request.json.get('receiver_id')
    content = request.json.get('content')
    
    if not content or not receiver_id:
        return jsonify({'error': 'Missing content or receiver'}), 400
    
    # Check if they are friends
    friendship_status = get_friendship_status(session['user_id'], receiver_id)
    if friendship_status != 'friends':
        return jsonify({'error': 'You can only message friends'}), 403
    
    # VULNERABLE: No sanitization on message content - XSS vulnerability
    conn = get_db_connection()
    
    # Insert user's message
    conn.execute('''
        INSERT INTO messages (sender_id, receiver_id, content)
        VALUES (?, ?, ?)
    ''', (session['user_id'], receiver_id, content))
    
    # Check if receiver is a dummy user (check if password is 'password123')
    receiver = conn.execute('SELECT * FROM users WHERE id = ?', (receiver_id,)).fetchone()
    is_dummy = False
    if receiver:
        # Check if this user has the default dummy password
        is_dummy = check_password_hash(receiver['password_hash'], 'password123')
        print(f"User {receiver['name']} (@{receiver['username']}) is dummy: {is_dummy}")  # Debug
    
    if is_dummy:
        print(f"Generating ML response for dummy user {receiver['name']}")  # Debug
        # Generate ML-based response from dummy user
        try:
            from chat_engine import chat_engine
            response = chat_engine.get_response(content, receiver['name'])
            print(f"Generated response: {response}")  # Debug
            
            # Insert dummy user's response
            conn.execute('''
                INSERT INTO messages (sender_id, receiver_id, content)
                VALUES (?, ?, ?)
            ''', (receiver_id, session['user_id'], response))
            
            print(f"SUCCESS: Dummy user {receiver['name']} responded")  # Debug
        except Exception as e:
            print(f"ERROR generating response: {e}")  # Debug
            import traceback
            traceback.print_exc()
            # Fallback response if chat engine fails
            fallback_response = "That's interesting! Tell me more about that."
            conn.execute('''
                INSERT INTO messages (sender_id, receiver_id, content)
                VALUES (?, ?, ?)
            ''', (receiver_id, session['user_id'], fallback_response))
            print(f"Used fallback response")  # Debug
    else:
        print(f"User {receiver['name'] if receiver else 'Unknown'} is not a dummy user")  # Debug
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Message sent'})

@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    other_user_id = request.json.get('user_id')
    
    if not other_user_id:
        return jsonify({'error': 'Missing user ID'}), 400
    
    # Check if they are friends
    friendship_status = get_friendship_status(session['user_id'], other_user_id)
    if friendship_status != 'friends':
        return jsonify({'error': 'You can only message friends'}), 403
    
    conn = get_db_connection()
    
    # Check if conversation already exists
    existing_messages = conn.execute('''
        SELECT COUNT(*) as count FROM messages 
        WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
    ''', (session['user_id'], other_user_id, other_user_id, session['user_id'])).fetchone()
    
    if existing_messages['count'] == 0:
        # Start new conversation - check if other user is dummy
        other_user = conn.execute('SELECT * FROM users WHERE id = ?', (other_user_id,)).fetchone()
        is_dummy = False
        if other_user:
            # Check if this user has the default dummy password
            is_dummy = check_password_hash(other_user['password_hash'], 'password123')
        
        if is_dummy:
            # Send conversation starter from dummy user
            try:
                starter_message = chat_engine.get_conversation_starter()
                conn.execute('''
                    INSERT INTO messages (sender_id, receiver_id, content)
                    VALUES (?, ?, ?)
                ''', (other_user_id, session['user_id'], starter_message))
                conn.commit()
            except Exception as e:
                print(f"ERROR generating starter: {e}")  # Debug
                # Fallback starter
                conn.execute('''
                    INSERT INTO messages (sender_id, receiver_id, content)
                    VALUES (?, ?, ?)
                ''', (other_user_id, session['user_id'], "Hey! How's it going?"))
                conn.commit()
    
    conn.close()
    return jsonify({'success': True, 'message': 'Conversation started'})

@app.route('/search_friends')
def search_friends():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'friends': []})
    
    conn = get_db_connection()
    
    # Search friends by name or username
    friends = conn.execute('''
        SELECT u.id, u.name, u.username, u.avatar
        FROM users u
        JOIN friends f ON (f.user1_id = u.id OR f.user2_id = u.id)
        WHERE (f.user1_id = ? OR f.user2_id = ?) 
        AND u.id != ?
        AND (LOWER(u.name) LIKE LOWER(?) OR LOWER(u.username) LIKE LOWER(?))
        ORDER BY u.name
    ''', (session['user_id'], session['user_id'], session['user_id'], f'%{query}%', f'%{query}%')).fetchall()
    
    conn.close()
    
    return jsonify({
        'friends': [{
            'id': friend['id'],
            'name': friend['name'],
            'username': friend['username'],
            'avatar': friend['avatar']
        } for friend in friends]
    })

@app.route('/get_messages/<int:user_id>')
def get_messages(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Check if they are friends
    friendship_status = get_friendship_status(session['user_id'], user_id)
    if friendship_status != 'friends':
        return jsonify({'error': 'You can only view messages from friends'}), 403
    
    conn = get_db_connection()
    messages = conn.execute('''
        SELECT m.*, 
               sender.name as sender_name, sender.username as sender_username, sender.avatar as sender_avatar,
               receiver.name as receiver_name, receiver.username as receiver_username, receiver.avatar as receiver_avatar
        FROM messages m
        JOIN users sender ON m.sender_id = sender.id
        JOIN users receiver ON m.receiver_id = receiver.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.created_at ASC
    ''', (session['user_id'], user_id, user_id, session['user_id'])).fetchall()
    
    # Mark messages as read
    conn.execute('''
        UPDATE messages SET is_read = 1 
        WHERE sender_id = ? AND receiver_id = ?
    ''', (user_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'messages': [{
            'id': message['id'],
            'content': message['content'],  # VULNERABLE: Raw content returned - XSS vulnerability
            'sender_id': message['sender_id'],
            'receiver_id': message['receiver_id'],
            'sender_name': message['sender_name'],
            'sender_username': message['sender_username'],
            'sender_avatar': message['sender_avatar'],
            'receiver_name': message['receiver_name'],
            'receiver_username': message['receiver_username'],
            'receiver_avatar': message['receiver_avatar'],
            'is_read': message['is_read'],
            'timestamp': message['created_at']
        } for message in messages]
    })

@app.route('/get_conversations')
def get_conversations():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    
    # Get all users the current user has exchanged messages with
    conversations = conn.execute('''
        SELECT DISTINCT 
            CASE 
                WHEN m.sender_id = ? THEN m.receiver_id 
                ELSE m.sender_id 
            END as user_id,
            u.name, u.username, u.avatar,
            (SELECT content FROM messages 
             WHERE (sender_id = ? AND receiver_id = u.id) OR (sender_id = u.id AND receiver_id = ?)
             ORDER BY created_at DESC LIMIT 1) as last_message,
            (SELECT created_at FROM messages 
             WHERE (sender_id = ? AND receiver_id = u.id) OR (sender_id = u.id AND receiver_id = ?)
             ORDER BY created_at DESC LIMIT 1) as last_message_time,
            (SELECT COUNT(*) FROM messages 
             WHERE sender_id = u.id AND receiver_id = ? AND is_read = 0) as unread_count
        FROM messages m
        JOIN users u ON (u.id = m.sender_id OR u.id = m.receiver_id)
        WHERE (m.sender_id = ? OR m.receiver_id = ?) AND u.id != ?
        ORDER BY last_message_time DESC
    ''', (session['user_id'], session['user_id'], session['user_id'], 
          session['user_id'], session['user_id'], session['user_id'],
          session['user_id'], session['user_id'], session['user_id'])).fetchall()
    
    conn.close()
    
    return jsonify({
        'success': True,
        'conversations': [{
            'other_user': {
                'id': conv['user_id'],
                'name': conv['name'],
                'username': conv['username'],
                'avatar': conv['avatar'] or f"https://via.placeholder.com/50x50/1877f2/ffffff?text={conv['name'][0]}"
            },
            'last_message': conv['last_message'],  # VULNERABLE: Raw content - XSS vulnerability
            'last_message_time': conv['last_message_time'],
            'unread_count': conv['unread_count']
        } for conv in conversations]
    })

@app.route('/get_user_info/<int:user_id>')
def get_user_info(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT id, name, username, avatar FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'username': user['username'],
            'avatar': user['avatar'] or f"https://via.placeholder.com/50x50/1877f2/ffffff?text={user['name'][0]}"
        }
    })

# Initialize database and populate sample data
if __name__ == '__main__':
    init_db()
    populate_sample_data()
    app.run(debug=True)
