from app import create_app
from extensions import db
from models import User, Application, Document, StatusUpdate, Notification
from werkzeug.security import generate_password_hash

def init_db():
    app = create_app()
    
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create a default agency user
        admin = User(
            username='admin',
            email='admin@dastaavej.com',  # Replace with actual email during deployment
            role='agency',
            is_verified=True
        )
        admin.set_password('admin123')  # Replace with actual password during deployment
        
        db.session.add(admin)
        db.session.commit()
        
        print("Database initialized successfully!")
        print("Default agency account created:")
        print("Username: admin")
        print("Password: admin123")
        print("Please change these credentials in production!")

if __name__ == '__main__':
    init_db()