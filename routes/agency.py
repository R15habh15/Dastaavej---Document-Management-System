from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, jsonify
from flask_login import login_required, current_user
from models import Application, StatusUpdate, Notification, User, Document
from extensions import db, mail
from flask_mail import Message
from forms import UpdateStatusForm
import tempfile
import os
import time
from utils import generate_application_pdf

agency_bp = Blueprint('agency', __name__)

@agency_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'agency':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Define the status variable
    status = request.args.get('status', 'pending')  # Default to 'pending' if not provided

    applications = Application.query.filter_by(status=status).order_by(Application.created_at.desc()).all()
    return render_template('agency/review-applications.html', 
                         applications=applications,
                         current_status=status)

@agency_bp.route('/update-status/<int:application_id>', methods=['GET', 'POST'])
@login_required
def update_status(application_id):
    if current_user.role != 'agency':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    application = Application.query.get_or_404(application_id)
    
    # Prevent updating applications that are already approved or rejected
    if application.status in ['approved', 'rejected']:
        flash('This application has been finalized and cannot be updated further', 'warning')
        return redirect(url_for('agency.review_applications', status=application.status))
    
    form = UpdateStatusForm()
    
    if form.validate_on_submit():
        application.status = form.status.data
        
        status_update = StatusUpdate(
            application_id=application.id,
            status=form.status.data,
            comment=form.comment.data,
            updated_by=current_user.id
        )
        
        # Get the citizen's email
        citizen = User.query.get(application.user_id)
        notification_title = f"Application Status Updated"
        notification_message = f"Your {application.document_type} application ({application.application_number}) status has been updated to {form.status.data}."
        
        # Create notification for the citizen
        notification = Notification(
            user_id=application.user_id,
            notification_title=notification_title,
            message=notification_message,
            is_read=False
        )
        
        # Send email notification
        msg = Message(
            subject=notification_title,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[citizen.email]
        )
        msg.body = f"""
Dear {citizen.username},

{notification_message}

Additional Comments: {form.comment.data if form.comment.data else 'No comments provided'}

You can check the details by logging into your Dastaavej dashboard.

Best regards,
Dastaavej Team
"""
        
        # Inside the update_status function, update the try-except block:
        try:
            db.session.add(status_update)
            db.session.add(notification)
            db.session.commit()
            
            # Send email notification
            mail.send(msg)
            flash('Application status updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating status: {str(e)}', 'danger')  # Include error details
            return redirect(url_for('agency.review_applications', status=application.status))
        
        return redirect(url_for('agency.review_applications', status=application.status))
    
    # Get all documents for this application
    documents = Document.query.filter_by(application_id=application_id).all()
    
    # Get status updates
    status_updates = StatusUpdate.query.filter_by(application_id=application_id).order_by(StatusUpdate.updated_at.desc()).all()
    
    return render_template('agency/update-status.html', 
                         application=application,
                         form=form,
                         status_updates=status_updates,
                         documents=documents)


@agency_bp.route('/review-applications')
@agency_bp.route('/review-applications/<status>')
@login_required
def review_applications(status='pending'):
    if current_user.role != 'agency':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    applications = Application.query.filter_by(status=status).order_by(Application.created_at.desc()).all()
    return render_template('agency/review-applications.html', 
                         applications=applications,
                         current_status=status)

@agency_bp.route('/view-application/<int:application_id>')
@login_required
def view_application_form(application_id):
    """View the application form in the browser"""
    if current_user.role != 'agency':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the application
    application = Application.query.get_or_404(application_id)
    
    # Find the application form document
    application_form = Document.query.filter_by(
        application_id=application.id, 
        document_type='application_form'
    ).first()
    
    if application_form:
        # If we have a stored application form document, serve it
        # Check if it's a Google Drive ID
        if len(application_form.file_path) > 25 and not os.path.exists(application_form.file_path):
            try:
                # Create a temporary file for viewing
                temp_dir = os.path.join(current_app.root_path, 'uploads', 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Create a unique filename with timestamp
                timestamp = int(time.time())
                temp_pdf_path = os.path.join(temp_dir, f"temp_application_{application_id}_{timestamp}.pdf")
                
                # Download from Google Drive
                from drive_api import download_from_drive, get_drive_preview_url
                
                # Get the preview URL from Google Drive
                preview_url = get_drive_preview_url(application_form.file_path)
                if preview_url:
                    # Redirect to Google Drive preview
                    return redirect(preview_url)
                else:
                    # Fallback to downloading and displaying locally
                    download_from_drive(application_form.file_path, temp_pdf_path)
                    return send_file(
                        temp_pdf_path,
                        mimetype='application/pdf'
                    )
            except Exception as e:
                flash(f'Error viewing application form: {str(e)}', 'danger')
                return redirect(url_for('agency.dashboard'))
        else:
            # Local file
            try:
                return send_file(
                    application_form.file_path,
                    mimetype='application/pdf'
                )
            except Exception as e:
                flash(f'Error viewing application form: {str(e)}', 'danger')
                return redirect(url_for('agency.dashboard'))
    else:
        # Generate the application form on-the-fly
        # Get application data
        application_data = {
            'full_name': application.name,
            'application_number': application.application_number,
            'document_type': application.document_type,
            'date_of_birth': application.dob.strftime('%Y-%m-%d') if application.dob else 'Not provided',
            'gender': application.gender,
            'address': application.address,
            'status': application.status,
            'created_at': application.created_at.strftime('%Y-%m-%d'),
            # Add more fields as needed
        }
        
        # Find the photo document
        photo_doc = Document.query.filter_by(
            application_id=application.id, 
            document_type='photo'
        ).first()
        
        photo_path = None
        temp_photo_path = None
        
        if photo_doc:
            try:
                # Create uploads directory if it doesn't exist
                uploads_dir = os.path.join(current_app.config['BASE_DIR'], 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                
                # Download the photo from Google Drive
                from drive_api import download_from_drive
                
                # Determine file extension
                if '.' in photo_doc.file_path:
                    file_extension = '.' + photo_doc.file_path.rsplit('.', 1)[1].lower()
                else:
                    file_extension = '.jpg'  # Default to jpg
                
                temp_photo_path = os.path.join(uploads_dir, f"temp_photo_{application_id}{file_extension}")
                download_from_drive(photo_doc.file_path, temp_photo_path)
                photo_path = temp_photo_path
            except Exception as e:
                flash(f'Error downloading photo: {str(e)}', 'warning')
                photo_path = None
        
        # Create a temporary directory for the PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get the app instance
            app = current_app
            
            # Generate the PDF
            pdf_path = generate_application_pdf(
                app,
                application_data, 
                photo_path, 
                application.document_type,
                temp_dir
            )
            
            # Return the PDF file as a download
            return send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=False,
                download_name=f"{application.document_type}_application_{application.application_number}.pdf"
            )

@agency_bp.route('/download-application/<int:application_id>')
@login_required
def download_application_form(application_id):
    """Download the application form"""
    if current_user.role != 'agency':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the application
    application = Application.query.get_or_404(application_id)
    
    # Find the application form document
    application_form = Document.query.filter_by(
        application_id=application.id, 
        document_type='application_form'
    ).first()
    
    if application_form:
        try:
            # Create a temporary file
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, f"application_{application_id}.pdf")
            
            # Download the file from Google Drive
            from drive_api import download_from_drive
            download_success = download_from_drive(application_form.file_path, temp_file)
            
            if not download_success:
                flash('Failed to download application form', 'danger')
                return redirect(url_for('agency.application_details', application_id=application_id))
            
            # Send the file to the user
            return send_file(
                temp_file,
                as_attachment=True,
                download_name=f"{application.application_number}_application.pdf",
                mimetype='application/pdf'
            )
        except Exception as e:
            current_app.logger.error(f"Error downloading application form: {str(e)}")
            flash('Error downloading application form', 'danger')
            return redirect(url_for('agency.application_details', application_id=application_id))
    else:
        # Generate the application form on-the-fly
        # Get application data
        application_data = {
            'full_name': application.name,
            'application_number': application.application_number,
            'document_type': application.document_type,
            'date_of_birth': application.dob.strftime('%Y-%m-%d') if application.dob else 'Not provided',
            'gender': application.gender,
            'address': application.address,
            'status': application.status,
            'created_at': application.created_at.strftime('%Y-%m-%d'),
            # Add more fields as needed
        }
        
        # Find the photo document
        photo_doc = Document.query.filter_by(
            application_id=application.id, 
            document_type='photo'
        ).first()
        
        photo_path = None
        if photo_doc:
            photo_path = os.path.join('uploads', photo_doc.file_path)
        
        # Create a temporary directory for the PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get the app instance
            app = current_app
            
            # Generate the PDF
            pdf_path = generate_application_pdf(
                app,
                application_data, 
                photo_path, 
                application.document_type,
                temp_dir
            )
            
            # Return the PDF file as a download
            return send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"{application.document_type}_application_{application.application_number}.pdf"
            )

@agency_bp.route('/view-document/<int:document_id>')
@login_required
def view_document(document_id):
    """View a document in the browser"""
    if current_user.role != 'agency':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the document
    document = Document.query.get_or_404(document_id)
    
    # Check if it's an image type document
    is_image = document.document_type in ['photo', 'signature'] or (
        hasattr(document, 'file_name') and 
        document.file_name and 
        document.file_name.lower().endswith(('.jpg', '.jpeg', '.png'))
    )
    
    try:
        # For images, use direct Google Drive URL
        if is_image:
            from drive_api import get_direct_image_url
            direct_url = get_direct_image_url(document.file_path)
            if direct_url:
                return redirect(direct_url)
        
        # For non-images or if direct URL fails, use the existing approach
        # Create a temporary file for viewing
        temp_dir = os.path.join(current_app.root_path, 'uploads', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create a unique filename with timestamp
        timestamp = int(time.time())
        
        # Determine file extension based on document type
        if is_image:
            # For photos, use jpg extension
            if document.document_type == 'photo':
                file_ext = 'jpg'
            # For signatures, use png extension
            elif document.document_type == 'signature':
                file_ext = 'png'
            # Otherwise try to get extension from filename or default to jpg
            elif hasattr(document, 'file_name') and document.file_name and '.' in document.file_name:
                file_ext = document.file_name.rsplit('.', 1)[1].lower()
            else:
                file_ext = 'jpg'
        else:
            file_ext = 'pdf'
            
        temp_file_path = os.path.join(temp_dir, f"temp_doc_{document_id}_{timestamp}.{file_ext}")
        
        # Download from Google Drive
        from drive_api import download_from_drive
        download_success = download_from_drive(document.file_path, temp_file_path)
        
        if download_success:
            # For images, serve the file directly
            if is_image:
                # Determine the correct MIME type based on extension
                if file_ext.lower() == 'png':
                    mimetype = 'image/png'
                elif file_ext.lower() in ['jpg', 'jpeg']:
                    mimetype = 'image/jpeg'
                else:
                    mimetype = f'image/{file_ext}'
                    
                # Log the file path and mimetype for debugging
                current_app.logger.info(f"Serving image: {temp_file_path} with mimetype: {mimetype}")
                
                return send_file(
                    temp_file_path,
                    mimetype=mimetype,
                    as_attachment=False
                )
            else:
                # For PDFs and other documents, try to use Google Drive preview
                from drive_api import get_drive_preview_url
                preview_url = get_drive_preview_url(document.file_path)
                
                if preview_url:
                    # Redirect to Google Drive preview
                    return redirect(preview_url)
                else:
                    # Fallback to local file
                    mimetype = 'application/pdf'
                    if hasattr(document, 'mime_type') and document.mime_type:
                        mimetype = document.mime_type
                    
                    return send_file(
                        temp_file_path,
                        mimetype=mimetype
                    )
        else:
            flash('Failed to download document', 'danger')
            return redirect(url_for('agency.application_details', application_id=document.application_id))
    except Exception as e:
        current_app.logger.error(f"Error viewing document: {str(e)}")
        flash(f'Error viewing document: {str(e)}', 'danger')
        return redirect(url_for('agency.application_details', application_id=document.application_id))


@agency_bp.route('/application-details/<int:application_id>')
@login_required
def application_details(application_id):
    """View application details"""
    if current_user.role != 'agency':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the application
    application = Application.query.get_or_404(application_id)
    
    # Get the user who submitted the application
    user = User.query.get(application.user_id)
    
    # Get status updates
    status_updates = StatusUpdate.query.filter_by(application_id=application.id).order_by(StatusUpdate.updated_at.desc()).all()
    
    return render_template('agency/application_details.html', 
                          application=application,
                          user=user,
                          status_updates=status_updates)