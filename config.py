import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    
    SECRET_KEY = os.getenv("SECRET_KEY", "6cc18fed0f55551fba55c742f42655cd")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///" + os.path.join(INSTANCE_DIR, "dastaavej.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Fix upload folder path
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Google Drive API Credentials
    GOOGLE_DRIVE_CREDENTIALS = os.path.join(BASE_DIR, "dastaavej-drive-api.json")
    
    # Mail Settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "officialdastaavej@gmail.com"
    MAIL_PASSWORD = "laxn onoj qwoo ksmw"
    MAIL_DEFAULT_SENDER = ("Dastaavej Document Services", "officialdastaavej@gmail.com")  # Use tuple format with name
    MAIL_USE_SSL = False
    MAIL_DEBUG = False  # Set to False in production

