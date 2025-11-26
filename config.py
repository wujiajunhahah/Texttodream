import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dreams.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # File Upload
    UPLOAD_FOLDER = os.path.join('static', 'models')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    
    # Mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # API Keys
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    TRIPO_API_KEY = os.getenv('TRIPO_API_KEY')
    
    # Session
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', 1800))
    
    # WTF
    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY', 'csrf_secret_key_2024')
    
    # Allowed Extensions
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'json,obj,fbx,glb,gltf').split(','))

    # Languages
    LANGUAGES = ['en', 'zh']
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_TRANSLATION_DIRECTORIES = 'translations'
