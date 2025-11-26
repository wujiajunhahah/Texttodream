import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dreams.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 安全配置
    SECRET_KEY = 'your-secret-key-here'  # 建议使用随机生成的密钥
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join('static', 'models')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 最大50MB
    
    # 邮件配置
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # API密钥
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    TRIPO_API_KEY = os.getenv('TRIPO_API_KEY')
    
    # 会话配置
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', 1800))  # 30分钟
    
    # 安全配置
    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY', 'csrf_secret_key_2024')
    
    # 文件上传配置
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'json,obj,fbx,glb,gltf').split(',')) 