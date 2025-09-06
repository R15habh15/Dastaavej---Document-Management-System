from flask_login import UserMixin
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'citizen' or 'agency'
    government_id = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Relationships
    applications = db.relationship('Application', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    status_updates = db.relationship('StatusUpdate', backref='updater', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    application_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Personal information
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    
    # PAN Card specific fields
    father_name = db.Column(db.String(100))
    aadhaar_number = db.Column(db.String(12))
    
    # Passport specific fields
    next_of_kin = db.Column(db.String(100))
    next_of_kin_relation = db.Column(db.String(50))
    next_of_kin_phone = db.Column(db.String(15))
    
    # Relationships
    documents = db.relationship('Document', backref='application', lazy=True, cascade="all, delete-orphan")
    status_updates = db.relationship('StatusUpdate', backref='application', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Application {self.application_number}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255))  # Make sure this field exists
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    mime_type = db.Column(db.String(100))  # MIME type
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Document {self.document_type} for Application {self.application_id}>'

class StatusUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StatusUpdate {self.status} for Application {self.application_id}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'
