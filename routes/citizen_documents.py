from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app, send_file
from flask_login import login_required, current_user
import os
import uuid
import tempfile
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from models import Application, Document
from extensions import db
from forms import UploadDocumentForm
from drive_api import download_from_drive, get_drive_preview_url
from routes.citizen_helpers import check_citizen_access, allowed_file, upload_document_to_drive

def register_document_routes(bp):
    @bp.route('/upload-documents', methods=['GET', 'POST'])
    @login_required
    def upload_documents():
        if current_user.role != 'citizen':
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        form = UploadDocumentForm()
        if form.validate_on_submit():
            try:
                # Process file uploads
                document_type = form.document_type.data
                
                # Generate unique application number
                application_number = f"{document_type.upper()}-{str(uuid.uuid4())[:8]}"
            
                new_application = Application(
                    user_id=current_user.id,
                    document_type=document_type,
                    application_number=application_number,
                    status='pending',
                    name=current_user.username,
                    dob=datetime.now(),
                    gender='not_specified',
                    address='not_specified'
                )
            
                db.session.add(new_application)
                db.session.flush()
            
                # File Uploads
                if document_type == 'passport':
                    files = {
                        'id_proof': form.id_proof.data,
                        'photo': form.photo.data,
                        'address_proof': form.address_proof.data,
                        'dob_proof': form.dob_proof.data
                    }
                else:  # pancard
                    files = {
                        'id_proof': form.pan_id_proof.data,
                        'photo': form.pan_photo.data,
                        'address_proof': form.pan_address_proof.data,
                        'signature': form.pan_signature.data
                    }
                
                # Create temp directory for file processing
                with tempfile.TemporaryDirectory() as temp_dir:
                    for field_name, file in files.items():
                        if file and allowed_file(file.filename):
                            # Upload to Google Drive
                            drive_file_id = upload_document_to_drive(file, application_number, field_name, temp_dir)
                            
                            new_document = Document(
                                application_id=new_application.id,
                                document_type=field_name,
                                file_path=drive_file_id
                            )
                            db.session.add(new_document)
            
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Documents uploaded successfully',
                    'redirect': url_for('citizen.dashboard')
                })
                    
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': str(e)}), 400

        if form.errors:
            return jsonify({'success': False, 'error': 'Invalid form data', 'errors': form.errors}), 400
        
        if request.method == 'GET':
            return render_template('citizen/upload-documents.html', form=form)
        
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    @bp.route('/view-document/<int:application_id>/<doc_type>')
    @login_required
    def view_document(application_id, doc_type):
        """View a document in the browser"""
        if not check_citizen_access():
            return redirect(url_for('main.index'))
        
        # Get the application
        application = Application.query.get_or_404(application_id)
        
        # Check if the application belongs to the current user
        if application.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('citizen.dashboard'))
        
        # Get the document
        document = Document.query.filter_by(application_id=application_id, document_type=doc_type).first()
        
        if not document:
            flash(f'Document not found', 'danger')
            return redirect(url_for('citizen.application_status', application_id=application_id))
        
        # Get the preview URL
        preview_url = get_drive_preview_url(document.file_path)
        
        if not preview_url:
            flash('Unable to generate preview link', 'danger')
            return redirect(url_for('citizen.application_status', application_id=application_id))
        
        # Redirect to the preview URL
        return redirect(preview_url)

    @bp.route('/download-document/<int:application_id>/<doc_type>')
    @login_required
    def download_document(application_id, doc_type):
        """Download a document"""
        if not check_citizen_access():
            return redirect(url_for('main.index'))
        
        # Get the application
        application = Application.query.get_or_404(application_id)
        
        # Check if the application belongs to the current user
        if application.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('citizen.dashboard'))
        
        # Get the document
        document = Document.query.filter_by(application_id=application_id, document_type=doc_type).first()
        
        if not document:
            flash(f'Document not found', 'danger')
            return redirect(url_for('citizen.application_status', application_id=application_id))
        
        try:
            # Create a temporary file
            temp_dir = tempfile.mkdtemp()
            file_extension = 'pdf'  # Default extension
            if hasattr(document, 'file_name') and document.file_name:
                file_extension = document.file_name.split('.')[-1]
                
            temp_file = os.path.join(temp_dir, f"{doc_type}.{file_extension}")
            
            # Download the file from Google Drive
            download_from_drive(document.file_path, temp_file)
            
            # Send the file to the user
            return send_file(
                temp_file,
                as_attachment=True,
                download_name=getattr(document, 'file_name', f"{doc_type}.{file_extension}"),
                mimetype=getattr(document, 'mime_type', 'application/octet-stream')
            )
        except Exception as e:
            current_app.logger.error(f"Error downloading document: {str(e)}")
            flash('Error downloading document', 'danger')
            return redirect(url_for('citizen.application_status', application_id=application_id))

    @bp.route('/view-application/<int:application_id>')
    @login_required
    def view_application_form(application_id):
        """View the application form in the browser"""
        if not check_citizen_access():
            return redirect(url_for('main.index'))
        
        # Get the application
        application = Application.query.filter_by(id=application_id, user_id=current_user.id).first_or_404()
        
        # Find the application form document
        application_form = Document.query.filter_by(
            application_id=application.id, 
            document_type='application_form'
        ).first()
        
        # Add debugging information
        current_app.logger.info(f"Application ID: {application_id}, Application form found: {application_form is not None}")
        
        # Check if application_form exists
        if not application_form:
            # Check if there are any documents for this application
            all_docs = Document.query.filter_by(application_id=application.id).all()
            current_app.logger.info(f"Total documents for application {application_id}: {len(all_docs)}")
            if all_docs:
                doc_types = [doc.document_type for doc in all_docs]
                current_app.logger.info(f"Document types: {doc_types}")
            
            flash('Application form not found', 'warning')
            return redirect(url_for('citizen.application_status', application_id=application_id))
        
        # If we have a stored application form document, serve it
        if len(application_form.file_path) > 25 and not os.path.exists(application_form.file_path):
            try:
                # Attempt to get the preview URL from Google Drive
                preview_url = get_drive_preview_url(application_form.file_path)
                current_app.logger.info(f"Preview URL: {preview_url}")
                if preview_url:
                    return redirect(preview_url)
                else:
                    # Fallback to downloading and displaying locally
                    temp_dir = os.path.join(current_app.root_path, 'uploads', 'temp')
                    os.makedirs(temp_dir, exist_ok=True)
                    timestamp = int(time.time())
                    temp_pdf_path = os.path.join(temp_dir, f"temp_application_{application_id}_{timestamp}.pdf")
                    current_app.logger.info(f"Downloading to: {temp_pdf_path}")
                    download_from_drive(application_form.file_path, temp_pdf_path)
                    return send_file(temp_pdf_path, mimetype='application/pdf')
            except Exception as e:
                current_app.logger.error(f"Error viewing application form: {str(e)}")
                flash(f'Error viewing application form: {str(e)}', 'danger')
                return redirect(url_for('citizen.dashboard'))
        else:
            flash('Application form not found', 'warning')
            return redirect(url_for('citizen.application_status', application_id=application_id))

    @bp.route('/download-application/<int:application_id>')
    @login_required
    def download_application_form(application_id):
        """Download the application form"""
        if not check_citizen_access():
            return redirect(url_for('main.index'))
        
        # Get the application
        application = Application.query.filter_by(id=application_id, user_id=current_user.id).first_or_404()
        
        # Find the application form document
        application_form = Document.query.filter_by(
            application_id=application.id, 
            document_type='application_form'
        ).first()
        
        if not application_form:
            flash('Application form not found', 'warning')
            return redirect(url_for('citizen.application_status', application_id=application_id))
            
        try:
            # Create a temporary file
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, f"application_{application_id}.pdf")
            
            # Download the file from Google Drive
            download_from_drive(application_form.file_path, temp_file)
            
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
            return redirect(url_for('citizen.application_status', application_id=application_id))