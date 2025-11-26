from flask import Flask, render_template, request, send_file, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_bootstrap import Bootstrap
from flask_babel import Babel, gettext as _
import os
import sys
import json
import time
import requests
import subprocess
import sqlite3
from dotenv import load_dotenv
from tqdm import tqdm
import tenacity
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
import random
import string
from services import DreamToModelConverter

load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')

if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'your-secret-key-here':
    app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))
    
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dreams.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
mail = Mail(app)

# Babel Configuration
def get_locale():
    # Check if user has set a language preference in session
    if 'lang' in session:
        return session['lang']
    # Otherwise try to match the best language from the request
    return request.accept_languages.best_match(app.config['LANGUAGES'])

babel = Babel(app, locale_selector=get_locale)

login_manager.login_view = 'login'
login_manager.login_message = _("Please log in to access this page.")
login_manager.login_message_category = "info"

# Logging Configuration
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/dream_to_model.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Dream to 3D Model App Startup')

# Models (User & Dream)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dreams = db.relationship('Dream', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Dream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    title = db.Column(db.String(150), nullable=False, default="Untitled Dream")
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    blockchain = db.Column(db.String(50), nullable=True)
    price = db.Column(db.Float, nullable=True)
    trading_type = db.Column(db.String(50), nullable=True)
    royalty = db.Column(db.Float, nullable=True)
    preview_image = db.Column(db.String(255), nullable=True, default='default_preview.png')

    dream_text = db.Column(db.Text, nullable=False)
    model_file = db.Column(db.String(255))
    keywords = db.Column(db.Text)
    symbols = db.Column(db.Text)
    emotions = db.Column(db.Text)
    visual_description = db.Column(db.Text)
    interpretation = db.Column(db.Text)
    nft_tx_hash = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(50), default='pending')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.cli.command("create-admin")
def create_admin():
    """Create admin account"""
    admin = User(
        username='123',
        email='123@example.com',
        is_active=True,
        is_admin=True
    )
    admin.set_password('123')
    db.session.add(admin)
    db.session.commit()
    print('Test account created! Username/Password: 123')

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

@app.route('/')
def index():
    """Home Page"""
    try:
        recent_models = Dream.query.order_by(Dream.created_at.desc()).limit(6).all()
        return render_template('index.html', recent_models=recent_models)
    except Exception as e:
        app.logger.error(f"Home page load error: {str(e)}")
        return render_template('index.html', recent_models=[])

@app.route('/create_dream', methods=['GET', 'POST'])
@login_required
def create_dream():
    """Create Dream Page"""
    if request.method == 'POST':
        try:
            dream_title = request.form.get('dream_title', '').strip()
            dream_description = request.form.get('dream_description', '').strip()
            dream_mood = request.form.get('dream_mood', '')
            blockchain = request.form.get('blockchain', '')
            initial_price = request.form.get('initial_price', type=float)
            royalty = request.form.get('royalty', type=float)
            
            if not dream_title or not dream_description or not blockchain:
                flash(_('Please fill in all required fields'), 'error')
                return render_template('create_dream.html')
            
            if len(dream_description) < 50:
                flash(_('Dream description must be at least 50 characters'), 'error')
                return render_template('create_dream.html')
            
            new_model = Dream(
                title=dream_title,
                description=dream_description,
                dream_text=dream_description,
                blockchain=blockchain,
                price=initial_price or 0.1,
                royalty=royalty or 2.5,
                user_id=current_user.id,
                status='processing'
            )
            
            if dream_mood:
                new_model.tags = f"{new_model.tags},{dream_mood}" if new_model.tags else dream_mood
            
            db.session.add(new_model)
            db.session.commit()
            
            # Temporary sync completion for demo (should be async)
            new_model.status = 'completed'
            new_model.model_file = f'models/dream_{new_model.id}.glb'
            db.session.commit()
            
            flash(_('Dream created successfully!'), 'success')
            return redirect(url_for('model_detail', model_id=new_model.id))
            
        except Exception as e:
            app.logger.error(f"Create dream error: {str(e)}")
            flash(_('Error creating dream, please try again'), 'error')
            return render_template('create_dream.html')
    
    return render_template('create_dream.html')

dream_progress = {}

def update_dream_progress(dream_id, stage, progress, remaining_minutes, status=None):
    dream_progress[dream_id] = {
        'stage': stage,
        'progress': progress,
        'remaining_minutes': remaining_minutes,
        'status': status or _("Processing...")
    }

@app.route('/api/progress/<dream_id>', methods=['GET'])
def get_progress(dream_id):
    try:
        dream_id = int(dream_id)
    except ValueError:
        return jsonify({"success": False, "error": _("Invalid Dream ID")}), 400
    
    dream = Dream.query.get(dream_id)
    if not dream:
        return jsonify({"success": False, "error": _("Dream not found")}), 404
    
    if dream_id not in dream_progress:
        if dream.status == 'complete':
            return jsonify({
                "success": True,
                "stage": _("Completed"),
                "progress": 100,
                "remaining_minutes": 0,
                "status": _("Your dream model is ready!")
            })
        elif dream.status == 'failed':
            return jsonify({
                "success": False,
                "stage": _("Failed"),
                "progress": 0,
                "status": _("Model generation failed, please retry.")
            }), 500
        elif dream.status == 'processing':
            update_dream_progress(dream_id, _("Analyzing Dream"), 10, 15, _("Analyzing your dream description..."))
        else:  # pending
            update_dream_progress(dream_id, _("Pending"), 0, 20, _("Your request is queued..."))
    
    progress_data = dream_progress.get(dream_id, {
        "stage": _("Unknown"),
        "progress": 0,
        "remaining_minutes": 0,
        "status": _("Cannot retrieve progress")
    })
    
    return jsonify({
        "success": True,
        **progress_data
    })

@app.route('/api/dreams/create', methods=['POST'])
@login_required
def create_dream_api():
    try:
        title = request.form.get('title', 'Untitled Dream')
        description = request.form.get('description')
        tags = request.form.get('tags')
        blockchain = request.form.get('blockchain')
        price_str = request.form.get('price')
        trading_type = request.form.get('tradingType')
        royalty_str = request.form.get('royalty')

        if not description:
            return jsonify({'success': False, 'error': _('Dream description cannot be empty')}), 400
        
        price = None
        if price_str:
            try:
                price = float(price_str)
            except ValueError:
                return jsonify({'success': False, 'error': _('Price must be a number')}), 400
        
        royalty = None
        if royalty_str:
            try:
                royalty = float(royalty_str)
            except ValueError:
                return jsonify({'success': False, 'error': _('Royalty must be a number')}), 400

        new_dream = Dream(
            user_id=current_user.id,
            title=title,
            description=description,
            dream_text=description,
            tags=tags,
            blockchain=blockchain,
            price=price,
            trading_type=trading_type,
            royalty=royalty,
            status='pending'
        )
        db.session.add(new_dream)
        db.session.commit()
        
        dream_id = new_dream.id
        app.logger.info(f"Created new dream record, ID: {dream_id}")
        
        update_dream_progress(dream_id, _("Pending"), 0, 20, _("Your request is queued..."))
        
        import threading
        
        def process_dream_async(description, user_id, dream_id):
            with app.app_context():
                try:
                    dream = Dream.query.get(dream_id)
                    dream.status = 'processing'
                    db.session.commit()
                    
                    converter = DreamToModelConverter(app=app)
                    
                    def progress_callback(d_id, stage, prog, mins, status):
                        update_dream_progress(d_id, stage, prog, mins, status)
                        
                    result = converter.process_dream(
                        dream_text=description, 
                        user_id=user_id, 
                        dream_id=dream_id,
                        update_progress_callback=progress_callback
                    )
                    
                    if result and 'model_path' in result:
                        dream = Dream.query.get(dream_id)
                        dream.model_file = result['model_path']
                        dream.keywords = result.get('keywords', '')
                        dream.symbols = result.get('symbols', '')
                        dream.emotions = result.get('emotions', '')
                        dream.visual_description = result.get('visual_description', '')
                        dream.interpretation = result.get('interpretation', '')
                        dream.status = 'complete'
                        db.session.commit()
                        
                        update_dream_progress(dream_id, _("Completed"), 100, 0, _("Your dream model is ready!"))
                        app.logger.info(f"Dream {dream_id} processing complete")
                    else:
                        raise Exception("Model generation failed")
                        
                except Exception as e:
                    app.logger.error(f"Async processing failed for dream {dream_id}: {str(e)}")
                    try:
                        dream = Dream.query.get(dream_id)
                        dream.status = 'failed'
                        db.session.commit()
                    except:
                        pass
                    update_dream_progress(dream_id, _("Failed"), 0, 0, f"{_('Model generation failed')}: {str(e)}")
        
        threading.Thread(target=process_dream_async, args=(description, current_user.id, dream_id)).start()
        
        return jsonify({
            'success': True,
            'dream_id': dream_id,
            'message': _('Dream creation request submitted!')
        })
            
    except Exception as e:
        app.logger.error(f"Create dream API failed: {str(e)}")
        return jsonify({'success': False, 'error': f"{_('Server error')}: {str(e)}"}), 500

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/api/interpretation/<model_name>')
@login_required
def get_interpretation(model_name):
    dream_id = model_name.split('.')[0]
    dream = Dream.query.filter_by(id=dream_id).first()
    if not dream:
        return jsonify({'error': _('Dream not found')}), 404
    
    if dream.user_id != current_user.id:
        return jsonify({'error': _('Access denied')}), 403
    
    return jsonify({
        'keywords': dream.keywords.split(','),
        'symbols': dream.symbols.split(','),
        'emotions': dream.emotions.split(','),
        'visuals': dream.visual_description,
        'psychology': dream.interpretation
    })

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server error: {error}')
    return render_template('500.html'), 500

@app.errorhandler(413)
def too_large(error):
    app.logger.error(f'File too large: {request.url}')
    return render_template('413.html'), 413

@app.route('/model_library')
def model_library():
    models = [
        {
            'id': 1,
            'title': 'Dream Bus',
            'tags': ['Vehicle', 'City', 'Public Space'],
            'description': 'A futuristic bus model showcasing a modern vision of urban transportation.',
            'price': 0.5,
            'model_path': '/static/models/大巴.glb'
        },
        {
            'id': 2,
            'title': 'Kanye',
            'tags': ['Person', 'Art', 'Music'],
            'description': 'A model capturing the unique image of Kanye West.',
            'price': 0.8,
            'model_path': '/static/models/kanye.glb'
        },
        {
            'id': 3,
            'title': 'Untitled Scan',
            'tags': ['Scan', 'Experiment', 'Art'],
            'description': 'An experimental art piece created via 3D scanning.',
            'price': 0.3,
            'model_path': '/static/models/Untitled_Scan.glb'
        }
    ]
    return render_template('model_library.html', models=models)

@app.route('/model/<model_id>')
def model_detail(model_id):
    model = {
        'id': model_id,
        'title': 'Dream Model #' + str(model_id),
        'creator': 'Dreamer',
        'creation_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'price': 0.05,
        'currency': 'ETH',
        'tags': ['Fantasy', 'Abstract', 'Color'],
        'description': 'A dream scene automatically generated by AI from dream descriptions.',
        'model_path': f'static/models/dream_model_{model_id}.glb',
        'technical_info': {
            'polygons': random.randint(10000, 50000),
            'vertices': random.randint(5000, 25000),
            'format': 'glTF/GLB'
        }
    }
    return render_template('model_detail.html', model=model)

@app.route('/api/mint_nft/<model_id>', methods=['POST'])
def mint_nft_api(model_id):
    try:
        app.logger.info(f"Simulating NFT minting for Model ID {model_id}")
        time.sleep(random.uniform(3, 8))
        
        if random.random() < 0.8:
            fake_tx_hash = '0x' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))
            app.logger.info(f"Model ID {model_id} NFT minting simulated success, Hash: {fake_tx_hash}")
            return jsonify({'success': True, 'tx_hash': fake_tx_hash})
        else:
            app.logger.error(f"Model ID {model_id} NFT minting simulated failure")
            error_message = random.choice([_("Network congestion"), _("Insufficient Gas"), _("Contract failed")])
            return jsonify({'success': False, 'error': error_message}), 500

    except Exception as e:
        app.logger.error(f"NFT minting error (Model ID: {model_id}): {str(e)}")
        return jsonify({'success': False, 'error': _('Internal Server Error')}), 500

@app.route('/project_background')
def project_background():
    return render_template('project_background.html')

@app.route('/style-guide')
def style_guide():
    return render_template('style_guide.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/generate_tags', methods=['POST'])
def generate_tags():
    data = request.get_json()
    tags = ['Dream', 'Flight', 'Freedom', 'Explore', 'Adventure', 'Fantasy']
    return jsonify({'success': True, 'tags': tags})

@app.route('/my_dreams')
@login_required
def my_dreams():
    dreams = Dream.query.filter_by(user_id=current_user.id).all()
    return render_template('my_dreams.html', dreams=dreams)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(_('Login successful'), 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        flash(_('Invalid username or password'), 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash(_('Username already exists'), 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash(_('Email already registered'), 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(_('Registration successful, please login'), 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/api_docs')
def api_docs():
    """Render API documentation page"""
    return render_template('api_docs.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
