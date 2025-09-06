from flask import current_app, url_for
import random
import string
from datetime import datetime
from flask_mail import Message
from extensions import mail
import secrets
import os
import time
import uuid  # Add this import for UUID generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))
    
def send_otp_email(app, email, otp):
    """Send OTP via email"""
    with app.app_context():
        msg = Message(
            subject="Your Verification Code - Dastaavej",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email]
        )
        
        # Add important headers to reduce spam likelihood
        msg.extra_headers = {
            'List-Unsubscribe': '<mailto:unsubscribe@dastaavej.com>',
            'Precedence': 'bulk',
            'X-Auto-Response-Suppress': 'OOF, DR, RN, NRN, AutoReply'
        }
        
        # Plain text version
        msg.body = f"""Hello,

Your verification code for Dastaavej registration is: {otp}

This code is valid for 10 minutes. Please do not share it with anyone.

Best regards,
Dastaavej Team
"""
        
        # HTML version
        msg.html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Code</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #333;">Your Verification Code</h2>
        </div>
        
        <p>Hello,</p>
        
        <p>Your verification code for Dastaavej registration is:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <div style="font-size: 24px; letter-spacing: 5px; font-weight: bold; background-color: #f5f5f5; padding: 15px; border-radius: 4px;">{otp}</div>
        </div>
        
        <p>This code is valid for 10 minutes. Please do not share it with anyone.</p>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #777;">
            <p>Best regards,<br>Dastaavej Team</p>
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f"Error sending OTP email: {str(e)}")
        return False

def generate_verification_token():
    return secrets.token_urlsafe(32)

def send_agency_verification_email(app, user, token):
    with app.app_context():
        verification_link = url_for('auth.verify_agency', token=token, _external=True)
        
        msg = Message(
            subject="New Agency Official Registration Verification",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=["officialdastaavej@gmail.com"]
        )
        
        # Add important headers to reduce spam likelihood
        msg.extra_headers = {
            'List-Unsubscribe': '<mailto:unsubscribe@dastaavej.com>',
            'Precedence': 'bulk',
            'X-Auto-Response-Suppress': 'OOF, DR, RN, NRN, AutoReply'
        }
        
        # Plain text version
        msg.body = f"""
A new agency official has registered and requires verification:

Username: {user.username}
Email: {user.email}
Government ID: {user.government_id}

To verify this registration, click the following link:
{verification_link}

If you did not expect this registration, please ignore this email.

Best regards,
Dastaavej Team
"""
        
        # HTML version with button
        msg.html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agency Verification</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #333;">New Agency Official Registration</h2>
        </div>
        
        <p>A new agency official has registered and requires verification:</p>
        
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 4px; margin: 20px 0;">
            <p><strong>Username:</strong> {user.username}</p>
            <p><strong>Email:</strong> {user.email}</p>
            <p><strong>Government ID:</strong> {user.government_id}</p>
        </div>
        
        <p>Please verify this registration if you recognize this official:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_link}" style="background-color: #28a745; color: white; text-decoration: none; padding: 12px 25px; border-radius: 4px; font-weight: bold; display: inline-block;">Verify Official</a>
        </div>
        
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <p style="word-break: break-all;"><a href="{verification_link}" style="color: #007bff;">{verification_link}</a></p>
        
        <p>If you did not expect this registration, please ignore this email.</p>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #777;">
            <p>Best regards,<br>Dastaavej Team</p>
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            app.logger.error(f"Error sending agency verification email: {str(e)}")
            return False

def send_verification_confirmation_email(app, user):
    with app.app_context():
        msg = Message(
            subject="Your Agency Account has been Verified - Dastaavej",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        
        # Add important headers to reduce spam likelihood
        msg.extra_headers = {
            'List-Unsubscribe': '<mailto:officialdastaavej@gmail.com>',
            'Precedence': 'bulk',
            'X-Auto-Response-Suppress': 'OOF, DR, RN, NRN, AutoReply'
        }
        
        # Plain text version
        msg.body = f"""
Dear {user.username},

Your agency official account on Dastaavej has been verified. You can now log in and access the agency dashboard.

Best regards,
Dastaavej Team
"""
        
        # HTML version with better formatting
        msg.html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Verified</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #333;">Account Verified</h2>
        </div>
        
        <p>Dear {user.username},</p>
        
        <p>Your agency official account on Dastaavej has been verified. You can now log in and access the agency dashboard.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{url_for('auth.login', _external=True)}" style="background-color: #28a745; color: white; text-decoration: none; padding: 12px 25px; border-radius: 4px; font-weight: bold; display: inline-block;">Login to Dashboard</a>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #777;">
            <p>Best regards,<br>Dastaavej Team</p>
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            app.logger.error(f"Error sending verification confirmation email: {str(e)}")
            return False


# Add this to your existing utils.py file
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter as LETTER_SIZE
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch as INCH
from reportlab.lib.enums import TA_CENTER as TEXT_ALIGN_CENTER, TA_LEFT as TEXT_ALIGN_LEFT

def generate_application_pdf(app, application_data, photo_path, document_type, temp_dir):
    """
    Generate a PDF application form with embedded photo
    
    Args:
        app: Flask application instance for logging
        application_data: Dictionary containing application form data
        photo_path: Path to the applicant's photo
        document_type: Type of document (passport or pancard)
        temp_dir: Directory to save the temporary PDF file
        
    Returns:
        Path to the generated PDF file
    """
    try:
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        pdf_filename = f"{document_type}_application_{timestamp}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
         # Create the PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Modify existing styles instead of adding new ones
        heading_style = styles['Heading1']
        heading_style.alignment = TA_CENTER
        heading_style.fontSize = 16
        
        # Add a new style for centered normal text
        styles.add(ParagraphStyle(
            name='Normal_CENTER',
            parent=styles['Normal'],
            alignment=TA_CENTER
        ))
        
        # Content elements
        elements = []
        
        # Title
        if document_type == 'passport':  # Changed from application_type to document_type
            title = "PASSPORT APPLICATION FORM"
        else:
            title = "PAN CARD APPLICATION FORM"
            
        elements.append(Paragraph(title, heading_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add photo if it exists
        if os.path.exists(photo_path):
            img = Image(photo_path, width=1.5*inch, height=1.8*inch)
            elements.append(img)
            elements.append(Paragraph("Applicant Photo", styles['Normal_CENTER']))
            elements.append(Spacer(1, 0.25*inch))
        
        # Application details
        data = []
        
        # Common fields for both document types
        data.append(["Full Name:", application_data.get('full_name', '')])
        data.append(["Date of Birth:", application_data.get('date_of_birth', '')])
        data.append(["Gender:", application_data.get('gender', '')])
        
        # Permanent Address
        perm_address = (
            f"{application_data.get('permanent_address', '')}, "
            f"{application_data.get('permanent_state', '')}, "
            f"{application_data.get('permanent_pincode', '')}, "
            f"{application_data.get('permanent_country', '')}"
        )
        data.append(["Permanent Address:", perm_address])
        
        # Current Address
        curr_address = (
            f"{application_data.get('current_address', '')}, "
            f"{application_data.get('current_state', '')}, "
            f"{application_data.get('current_pincode', '')}, "
            f"{application_data.get('current_country', '')}"
        )
        data.append(["Current Address:", curr_address])
        
        # Contact information
        data.append(["Phone:", application_data.get('phone', '')])
        data.append(["Email:", application_data.get('email', '')])
        
        # Document-specific fields
        if document_type == 'passport':  # Changed from application_type to document_type
            data.append(["Next of Kin:", application_data.get('next_of_kin', '')])
            data.append(["Relation:", application_data.get('next_of_kin_relation', '')])
            data.append(["Next of Kin Phone:", application_data.get('next_of_kin_phone', '')])
        elif document_type == 'pancard':  # Changed from application_type to document_type
            data.append(["Father's Name:", application_data.get('father_name', '')])
            data.append(["Aadhaar Number:", application_data.get('aadhaar_number', '')])
        
        # Create table
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (1, 0), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        
        # Add application date
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(f"Application Date: {datetime.now().strftime('%d-%m-%Y')}", styles['Normal']))
        
        # Add declaration
        elements.append(Spacer(1, 0.5*inch))
        declaration = "I hereby declare that the information provided in this application is true and correct to the best of my knowledge."
        elements.append(Paragraph(declaration, styles['Normal']))
        
        # Add signature space
        elements.append(Spacer(1, inch))
        elements.append(Paragraph("Applicant's Signature", styles['Normal']))
        
        # Build the PDF
        doc.build(elements)
        
        # Log successful PDF creation
        app.logger.info(f"PDF successfully created at {pdf_path}")
        return pdf_path
    except Exception as e:
        # Log any errors that occur during PDF generation
        app.logger.error(f"Error generating PDF: {str(e)}")
        return None