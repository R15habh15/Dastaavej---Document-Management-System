# Dastaavej - Document Management System

A secure document management system built with Flask for handling passport and PAN card applications. Dastaavej helps citizens manage their document applications and allows government agencies to process them efficiently.

## Features

- User Authentication and Authorization
  - Secure user registration and login
  - Email verification
  - Password reset functionality
  - Role-based access control (Citizen/Agency)

- Document Management
  - Upload and store important documents
  - Secure Google Drive integration for document storage
  - Support for various document formats
  - Document versioning and tracking

- Application Processing
  - Apply for Passport and PAN Card
  - Track application status in real-time
  - Receive email notifications on status updates
  - Digital document verification

- Agency Dashboard
  - Review and process applications
  - Verify uploaded documents
  - Update application status
  - Manage citizen applications

## Technologies Used

- Backend
  - Python 3.13
  - Flask 3.0.0
  - SQLAlchemy (Database ORM)
  - Flask-Migrate (Database migrations)
  - Flask-Login (Authentication)
  - Flask-Mail (Email notifications)

- Frontend
  - HTML5/CSS3
  - JavaScript
  - Bootstrap 5
  - Responsive design

- Storage & APIs
  - SQLite Database
  - Google Drive API
  - Email validation

- Security
  - CSRF Protection
  - Secure password hashing
  - Form validation
  - Session management

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/dastaavej.git
cd dastaavej
```

2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up Google Drive API
   - Create a project in Google Cloud Console
   - Enable Google Drive API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the client configuration file as `dastaavej-drive-api.json`
   - Place it in the project root directory

5. Initialize the database
```bash
python init_db.py
```

6. Start the application
```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000`

## Environment Variables

Create a `.env` file in the project root with the following variables:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
```

## Project Structure
```
dastaavej/
├── app.py              # Application entry point
├── config.py           # Configuration settings
├── extensions.py       # Flask extensions
├── forms.py           # WTForms definitions
├── models.py          # Database models
├── utils.py           # Utility functions
├── drive_api.py       # Google Drive integration
├── routes/            # Route handlers
├── templates/         # HTML templates
├── static/           # Static files (CSS, JS)
├── migrations/       # Database migrations
└── instance/        # Instance-specific files
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Contributors

###Rishabh Tripathi
###Sumeet Prajapati
