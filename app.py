#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()
# Removed Flask-Login imports to simplify
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
migrate = Migrate(app, db)

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

# Simplified Data Model - No User Model needed for pure demo
class Dream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Dream attributes
    status = db.Column(db.String(20), default='completed')
    progress = db.Column(db.Integer, default=0)
    current_stage = db.Column(db.String(100), default='')
    estimated_time = db.Column(db.Integer, default=0) # in seconds
    
    # AI generated fields
    dream_text = db.Column(db.Text, nullable=True)
    model_file = db.Column(db.String(255))
    keywords = db.Column(db.Text)
    symbols = db.Column(db.Text)
    emotions = db.Column(db.Text)
    visual_description = db.Column(db.Text)
    interpretation = db.Column(db.Text)
    tags = db.Column(db.String(255))

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

# Routes - Simplified Flow
@app.route('/', methods=['GET', 'POST'])
def index():
    # Direct entry to creation, simplified home
    if request.method == 'POST':
        dream_description = request.form.get('dream_description', '').strip()
        dream_title = request.form.get('dream_title', '').strip() # Trigger word
        
        if not dream_description:
            flash(_('Please describe your dream'), 'error')
            return render_template('create_dream.html')
        
        new_model = Dream(
            title=dream_title or "Untitled Dream",
            description=dream_description,
            dream_text=dream_description,
            status='processing',
            progress=0,
            current_stage=_('Initializing...'),
            estimated_time=120 # Initial estimate 2 mins
        )
        
        db.session.add(new_model)
        db.session.commit()
        
        # Async processing setup
        import threading
        from services import DreamToModelConverter
        
        def update_progress(dream_id, stage, progress, remaining_minutes, status_text):
            with app.app_context():
                try:
                    dream = Dream.query.get(dream_id)
                    if dream:
                        dream.current_stage = status_text
                        dream.progress = progress
                        dream.estimated_time = remaining_minutes * 60
                        db.session.commit()
                except Exception as e:
                    print(f"Error updating progress: {e}")

        def process_dream_async(description, dream_id):
             with app.app_context():
                try:
                    converter = DreamToModelConverter(app=app)
                    # Real processing with callback
                    result = converter.process_dream(
                        dream_text=description, 
                        user_id=0, # Anonymous
                        dream_id=dream_id,
                        update_progress_callback=update_progress
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
                        dream.progress = 100
                        dream.current_stage = _('Completed')
                        db.session.commit()
                except Exception as e:
                    print(f"Error processing dream: {e}")
                    try:
                        dream = Dream.query.get(dream_id)
                        dream.status = 'failed'
                        dream.current_stage = f"Error: {str(e)}"
                        db.session.commit()
                    except:
                        pass

        threading.Thread(target=process_dream_async, args=(dream_description, new_model.id)).start()
        
        # Redirect directly to result page (will show processing state initially)
        return redirect(url_for('model_detail', model_id=new_model.id))
    
    return render_template('create_dream.html')

@app.route('/model/<model_id>')
def model_detail(model_id):
    dream = Dream.query.get_or_404(model_id)
    
    # Check status for polling
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': dream.status,
            'progress': dream.progress,
            'stage': dream.current_stage,
            'estimated_time': dream.estimated_time
        })
    
    model_data = {
        'id': dream.id,
        'title': dream.title,
        'description': dream.description,
        'creator': "Dreamer",
        'creation_date': dream.created_at.strftime('%Y-%m-%d %H:%M'),
        'tags': dream.tags.split(',') if dream.tags else [],
        'status': dream.status,
        'progress': dream.progress,
        'current_stage': dream.current_stage,
        'model_path': url_for('static', filename=dream.model_file) if dream.model_file else '',
        'interpretation': {
            'keywords': dream.keywords,
            'symbols': dream.symbols,
            'emotions': dream.emotions,
            'visual_description': dream.visual_description,
            'psychology': dream.interpretation
        }
    }
    return render_template('model_detail.html', model=model_data)

@app.route('/api/status/<model_id>')
def check_status(model_id):
    dream = Dream.query.get_or_404(model_id)
    return jsonify({
        'status': dream.status,
        'progress': dream.progress,
        'stage': dream.current_stage
    })

# Removed Login/Register/Profile routes

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# DB Initialization
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("DreamEcho running on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
