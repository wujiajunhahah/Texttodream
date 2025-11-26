#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from flask_babel import Babel, gettext as _
from flask_migrate import Migrate

# Create Flask app
app = Flask(__name__)

# Config
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dreams.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Babel Configuration for i18n
app.config['LANGUAGES'] = ['en', 'zh']
app.config['BABEL_DEFAULT_LOCALE'] = 'en'

def get_locale():
    if 'lang' in session:
        return session['lang']
    return request.accept_languages.best_match(app.config['LANGUAGES'])

babel = Babel(app, locale_selector=get_locale)

# Performance optimization: Add cache headers
@app.after_request
def after_request(response):
    if request.endpoint == 'static':
        response.cache_control.max_age = 31536000  # 1 year
        response.cache_control.public = True
    elif response.content_type.startswith('text/html'):
        response.cache_control.max_age = 300  # 5 minutes
        response.cache_control.public = True
    
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response

# Data Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True) # Default active for simplicity
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    dreams = db.relationship('Dream', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Dream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Dream attributes
    mood = db.Column(db.String(50))
    style = db.Column(db.String(50))
    blockchain = db.Column(db.String(20), default='ethereum')
    price = db.Column(db.Float, default=0.1) # Renamed from initial_price for consistency
    royalty = db.Column(db.Float, default=2.5)
    is_public = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='completed')
    
    # AI generated fields (for compatibility with services.py)
    dream_text = db.Column(db.Text, nullable=True) # Can be same as description
    model_file = db.Column(db.String(255))
    keywords = db.Column(db.Text)
    symbols = db.Column(db.Text)
    emotions = db.Column(db.Text)
    visual_description = db.Column(db.Text)
    interpretation = db.Column(db.Text)
    tags = db.Column(db.String(255)) # Comma separated tags
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Language Switching Route
@app.route('/set_language/<language>')
def set_language(language=None):
    if language in app.config['LANGUAGES']:
        session['lang'] = language
    return redirect(request.referrer or url_for('index'))

# Context Processor for Language
@app.context_processor
def inject_conf_var():
    return dict(
        CURRENT_LANGUAGE=session.get('lang', request.accept_languages.best_match(app.config['LANGUAGES'])),
        AVAILABLE_LANGUAGES=app.config['LANGUAGES']
    )

# Routes
@app.route('/')
def index():
    # Ensure database tables exist before querying
    with app.app_context():
        db.create_all()
        
    try:
        recent_models = Dream.query.filter_by(is_public=True).order_by(Dream.created_at.desc()).limit(6).all()
    except Exception:
        recent_models = []
        
    return render_template('index.html', recent_models=recent_models)

@app.route('/create_dream', methods=['GET', 'POST'])
@login_required
def create_dream():
    if request.method == 'POST':
        dream_title = request.form.get('dream_title', '').strip()
        dream_description = request.form.get('dream_description', '').strip()
        dream_mood = request.form.get('dream_mood', '')
        dream_style = request.form.get('dream_style', '') # Capturing style if present in form
        blockchain = request.form.get('blockchain', '')
        initial_price = request.form.get('initial_price', type=float)
        is_public = 'is_public' in request.form
        
        if not dream_title or not dream_description or not blockchain:
            flash(_('Please fill in all required fields'), 'error')
            return render_template('create_dream.html')
        
        if len(dream_description) < 10: # Reduced limit for easier testing
            flash(_('Dream description must be at least 10 characters'), 'error')
            return render_template('create_dream.html')
        
        new_model = Dream(
            title=dream_title,
            description=dream_description,
            dream_text=dream_description, # For AI processing compatibility
            mood=dream_mood,
            style=dream_style,
            blockchain=blockchain,
            price=initial_price or 0.1,
            is_public=is_public,
            user_id=current_user.id,
            status='processing' # Set to processing initially
        )
        
        db.session.add(new_model)
        db.session.commit()
        
        # Async processing setup (simplified here, ideally should use services.py logic)
        import threading
        from services import DreamToModelConverter
        
        def process_dream_async(description, user_id, dream_id):
             with app.app_context():
                try:
                    # Simulate processing or call actual service
                    converter = DreamToModelConverter(app=app)
                    # For now, we just mark complete to mimic original behavior but we could use converter.process_dream
                    # To keep it simple and working like the "original" code user provided but with DB structure:
                    dream = Dream.query.get(dream_id)
                    dream.status = 'complete' 
                    dream.model_file = f'models/dream_{dream.id}.glb' # Mock model path
                    db.session.commit()
                except Exception as e:
                    print(f"Error processing dream: {e}")

        threading.Thread(target=process_dream_async, args=(dream_description, current_user.id, new_model.id)).start()
        
        flash(_('Dream created successfully!'), 'success')
        return redirect(url_for('model_library'))
    
    return render_template('create_dream.html')

@app.route('/model_library')
def model_library():
    page = request.args.get('page', 1, type=int)
    try:
        models = Dream.query.filter_by(is_public=True).order_by(Dream.created_at.desc()).paginate(
            page=page, per_page=12, error_out=False
        )
    except Exception:
        models = None
        
    return render_template('model_library.html', models=models)

@app.route('/model/<model_id>')
def model_detail(model_id):
    dream = Dream.query.get_or_404(model_id)
    # Mocking some data if not present
    model_data = {
        'id': dream.id,
        'title': dream.title,
        'description': dream.description,
        'creator': dream.user.username,
        'creation_date': dream.created_at.strftime('%Y-%m-%d %H:%M'),
        'price': dream.price,
        'tags': [dream.mood] if dream.mood else [],
        'status': dream.status,
        'model_path': url_for('static', filename=dream.model_file) if dream.model_file else ''
    }
    return render_template('model_detail.html', model=model_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(_('Login successful'), 'success')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index')) # Changed to index as per common flow
        else:
            flash(_('Invalid username or password'), 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash(_('Username already exists'), 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash(_('Email already registered'), 'error')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash(_('Registration successful! Please login'), 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('Successfully logged out'), 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api_docs')
def api_docs():
    return render_template('api_docs.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# DB Initialization
with app.app_context():
    db.create_all()
    # Create default admin if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@dreamecho.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user: admin/admin123")

if __name__ == '__main__':
    print("DreamEcho running on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
