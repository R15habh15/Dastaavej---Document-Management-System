from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email, ValidationError
from flask_mail import Message
from extensions import mail

main_bp = Blueprint('main', __name__)

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    # Pass `enumerate` explicitly to Jinja
    privacy_questions = [
        ("What information do we collect?", "We collect personal details like name, email, and usage data."),
        ("How do we use your information?", "We use your data for processing applications and improving services."),
        ("How is my data protected?", "Your data is encrypted and stored securely."),
        ("Do we use cookies?", "Yes, we use cookies to improve user experience."),
        ("How can I delete my account?", "You can request account deletion in your profile settings.")
    ]
    
    return render_template('about.html', privacy_questions=privacy_questions, enumerate=enumerate)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            # Create email message
            msg = Message(
                subject=f"Contact Form Submission from {form.name.data}",
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=["officialdastaavej@gmail.com"], 
                reply_to=form.email.data
            )
            
            # Email body
            msg.body = f"""
New Contact Form Submission

Name: {form.name.data}
Email: {form.email.data}

Message:
{form.message.data}
"""
            
            # Send email
            mail.send(msg)
            
            # Send confirmation email to user
            confirm_msg = Message(
                subject="We've received your message - Dastaavej",
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[str(form.email.data)] if form.email.data else []
            )
            
            confirm_msg.body = f"""
Dear {form.name.data},

Thank you for contacting Dastaavej. We have received your message and will get back to you shortly.

Your message:
{form.message.data}

Best regards,
Dastaavej Support Team
"""
            mail.send(confirm_msg)
            
            flash('Your message has been sent successfully! We will get back to you soon.', 'success')
            return redirect(url_for('main.contact'))
            
        except Exception as e:
            flash('Sorry, there was an error sending your message. Please try again later.', 'danger')
            current_app.logger.error(f"Contact form error: {str(e)}")
    
    return render_template('contact.html', form=form)

@main_bp.route('/terms')
def terms():
    return render_template('legal/terms.html')

@main_bp.route('/privacy')
def privacy():
    return render_template('legal/privacy.html')

@main_bp.route('/test-email/<email>')
def test_email(email):
    try:
        msg = Message(
            subject="Test Email from Dastaavej",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email]
        )
        msg.body = "This is a test email from Dastaavej application."
        mail.send(msg)
        return f"Test email sent to {email}. Please check your inbox or spam folder."
    except Exception as e:
        return f"Error sending email: {str(e)}"

@main_bp.route('/test-smtp-email/<email>')
def test_smtp_email(email):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # Email details
        sender_email = "officialdastaavej@gmail.com"
        sender_password = "lpxg qnnz kdxe nego"  # Updated password
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Direct SMTP Test from Dastaavej"
        
        # Add body
        body = "This is a test email sent directly via SMTP from Dastaavej application."
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server and send
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        
        return f"Direct SMTP test email sent to {email}. Please check your inbox or spam folder."
    except Exception as e:
        return f"Error sending direct SMTP email: {str(e)}"