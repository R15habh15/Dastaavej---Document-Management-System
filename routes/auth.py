from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from extensions import db, login_manager, mail
from utils import generate_otp, send_otp_email, generate_verification_token, send_agency_verification_email, send_verification_confirmation_email
from forms import RegisterForm, OTPVerificationForm, ForgotPasswordForm, ResetPasswordForm
from models import User
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message

auth_bp = Blueprint('auth', __name__)

# Login form class
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('citizen.dashboard') if current_user.role == 'citizen' else url_for('agency.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if user.role == 'agency' and not user.is_verified:
                flash('Your agency account is pending verification. Please check your email.', 'warning')
                return render_template('login.html', form=form)
            
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('citizen.dashboard') if user.role == 'citizen' else url_for('agency.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()
    
    # Debug form submission
    if request.method == 'POST':
        print(f"Form submitted: {request.form}")
        
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data
        role = form.role.data
        government_id = form.government_id.data

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html', form=form)

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html', form=form)
        
        # For agency officials, create unverified account and send verification email
        if role == 'agency':
            user = User(username=username, email=email, role=role, government_id=government_id, is_verified=False)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Generate verification token
            verification_token = generate_verification_token()
            
            # Store verification data in cache or database
            cache_key = f'agency_verification_{verification_token}'
            verification_data = {
                'user_id': user.id,
                'timestamp': datetime.now().timestamp()
            }
            current_app.config['VERIFICATION_CACHE'][cache_key] = verification_data
            
            # Send verification email to admin
            app = current_app
            if send_agency_verification_email(app, user, verification_token):
                flash('Registration pending admin verification. You will be notified via email when approved.', 'info')
                return redirect(url_for('auth.login'))
            else:
                db.session.delete(user)
                db.session.commit()
                flash('Failed to process registration. Please try again.', 'danger')
        
        # For citizens, require OTP verification
        otp = generate_otp()
        app = current_app
        if send_otp_email(app, email, otp):
            # Store registration data in session
            session['registration_data'] = {
                'username': username,
                'email': email,
                'password': password,
                'role': role,
                'government_id': government_id,
                'otp': otp,
                'otp_time': datetime.now().timestamp()
            }
            flash('OTP sent to your email. Please verify to complete registration.', 'info')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('Failed to send OTP. Please try again.', 'danger')
            
    # Enhanced debugging for validation issues
    if form.errors:
        print(f"Form validation errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")
            
    return render_template('register.html', form=form)

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated or 'registration_data' not in session:
        return redirect(url_for('main.index'))
    
    form = OTPVerificationForm()
    if form.validate_on_submit():
        registration_data = session['registration_data']
        user_otp = form.otp.data
        stored_otp = registration_data['otp']
        otp_time = registration_data['otp_time']
        
        # Check if OTP is expired (10 minutes)
        if datetime.now().timestamp() - otp_time > 600:
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.resend_otp'))
        
        # Verify OTP
        if user_otp == stored_otp:
            # Create user
            user = User(
                username=registration_data['username'],
                email=registration_data['email'],
                role=registration_data['role'],
                government_id=registration_data.get('government_id', '')
            )
            user.set_password(registration_data['password'])
            db.session.add(user)
            db.session.commit()
            
            # Clear session data
            session.pop('registration_data', None)
            
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html', form=form)

@auth_bp.route('/resend-otp', methods=['GET'])
def resend_otp():
    if current_user.is_authenticated or 'registration_data' not in session:
        return redirect(url_for('main.index'))
    
    registration_data = session['registration_data']
    email = registration_data['email']
    
    # Generate new OTP
    new_otp = generate_otp()
    app = current_app
    if send_otp_email(app, email, new_otp):
        # Update session data
        registration_data['otp'] = new_otp
        registration_data['otp_time'] = datetime.now().timestamp()
        session['registration_data'] = registration_data
        
        flash('New OTP sent to your email.', 'info')
    else:
        flash('Failed to send OTP. Please try again.', 'danger')
    
    return redirect(url_for('auth.verify_otp'))

def get_reset_token(user):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(user.email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return User.query.filter_by(email=email).first()
    except:
        return None

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                token = get_reset_token(user)
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                
                # Create the email message
                msg = Message('Password Reset Request - Dastaavej',
                            sender=current_app.config['MAIL_DEFAULT_SENDER'],
                            recipients=[user.email])
                
                # Add important headers to reduce spam likelihood
                msg.extra_headers = {
                    'List-Unsubscribe': '<mailto:unsubscribe@dastaavej.com>',
                    'Precedence': 'bulk',
                    'X-Auto-Response-Suppress': 'OOF, DR, RN, NRN, AutoReply'
                }
                
                # Plain text version
                msg.body = f'''Hello {user.username},

We received a request to reset your password for your Dastaavej account.

To reset your password, please visit: {reset_url}

This link will expire in 1 hour.

If you did not make this request, please ignore this email and your password will remain unchanged.

Best regards,
Dastaavej Team
'''
                # HTML version with button
                msg.html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #333;">Password Reset Request</h2>
        </div>
        
        <p>Hello {user.username},</p>
        
        <p>We received a request to reset your password for your Dastaavej account. Please use the button below to set a new password:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #007bff; color: white; text-decoration: none; padding: 12px 25px; border-radius: 4px; font-weight: bold; display: inline-block;">Reset Password</a>
        </div>
        
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <p style="word-break: break-all;"><a href="{reset_url}" style="color: #007bff;">{reset_url}</a></p>
        
        <p>This link will expire in 1 hour.</p>
        
        <p>If you did not request a password reset, please ignore this email and your password will remain unchanged.</p>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #777;">
            <p>Best regards,<br>Dastaavej Team</p>
            <p>This is an automated message, please do not reply to this email.</p>
            <p>To unsubscribe from these notifications, please contact <a href="mailto:support@dastaavej.com">support@dastaavej.com</a></p>
        </div>
    </div>
</body>
</html>
'''
                # Send the email
                mail.send(msg)
                flash('An email has been sent with instructions to reset your password.', 'info')
                return redirect(url_for('auth.login'))
            except Exception as e:
                current_app.logger.error(f"Password reset email error: {str(e)}")
                flash('Error sending email. Please try again later.', 'danger')
        else:
            # For security reasons, don't reveal if email exists or not
            flash('If that email address is in our system, we will send a password reset link.', 'info')
            return redirect(url_for('auth.login'))
            
    return render_template('forgot-password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    user = verify_reset_token(token)
    if not user:
        flash('Invalid or expired reset token. Please request a new password reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('reset-password.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/verify-agency/<token>')
def verify_agency(token):
    cache_key = f'agency_verification_{token}'
    verification_data = current_app.config['VERIFICATION_CACHE'].get(cache_key)
    
    if not verification_data:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get(verification_data['user_id'])
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('main.index'))
    
    user.is_verified = True
    db.session.commit()
    
    # Remove verification data from cache
    current_app.config['VERIFICATION_CACHE'].pop(cache_key, None)
    
    # Send confirmation email to the agency official
    app = current_app
    send_verification_confirmation_email(app, user)
    
    flash('Agency official account has been verified.', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')
    if email:
        otp = generate_otp()
        app = current_app
        if send_otp_email(app, email, otp):
            # Store OTP in session
            session['otp'] = otp
            session['otp_email'] = email
            flash('OTP sent to your email', 'success')
        else:
            flash('Failed to send OTP', 'danger')
    return redirect(url_for('auth.register'))

@auth_bp.route('/register-agency', methods=['POST'])
def register_agency():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    government_id = request.form.get('government_id')
    
    # Basic validation
    if not all([username, email, password, government_id]):
        flash('All fields are required', 'danger')
        return redirect(url_for('auth.register'))
    
    # Create unverified agency user
    user = User(
        username=username,
        email=email,
        role='agency',
        government_id=government_id,
        is_verified=False
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Generate verification token and send email
        verification_token = generate_verification_token()
        
        # Store verification data
        cache_key = f'agency_verification_{verification_token}'
        verification_data = {
            'user_id': user.id,
            'timestamp': datetime.now().timestamp()
        }
        current_app.config['VERIFICATION_CACHE'][cache_key] = verification_data
        
        # Send verification email
        app = current_app
        if send_agency_verification_email(app, user, verification_token):
            flash('Registration pending admin verification. You will be notified via email when approved.', 'info')
        else:
            flash('Account created but verification email could not be sent.', 'warning')
            
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        flash(f'Registration failed: {str(e)}', 'danger')
        return redirect(url_for('auth.register'))