import os

class Config:
    SECRET_KEY = 'edu-share-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///edushare.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB