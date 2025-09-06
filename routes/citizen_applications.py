from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
import os
import uuid
import tempfile
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from models import Application, Document
from extensions import db
from forms import PassportApplicationForm, PassportDocumentForm, PanCardApplicationForm, PanCardDocumentForm
from drive_api import upload_to_drive
from utils import generate_application_pdf
from routes.citizen_helpers import check_citizen_access, allowed_file, upload_document_to_drive

def register_application_routes(bp):
    
    @bp.route('/passport-application', methods=['GET', 'POST'])
    @login_required
    def passport_application():
        if not check_citizen_access():
            flash('Access denied. You must be logged in as a citizen.', 'danger')
            return redirect(url_for('main.index'))
        
        form = PassportApplicationForm()
        if form.validate_on_submit():
            # Store form data in session
            session['passport_application_data'] = {
                'full_name': form.full_name.data,
                'date_of_birth': form.date_of_birth.data.strftime('%Y-%m-%d') if form.date_of_birth.data else None,
                'gender': form.gender.data,
                'permanent_address': form.permanent_address.data,
                'permanent_state': form.permanent_state.data,
                'permanent_pincode': form.permanent_pincode.data,
                'permanent_country': form.permanent_country.data,
                'current_address': form.current_address.data,
                'current_state': form.current_state.data,
                'current_pincode': form.current_pincode.data,
                'current_country': form.current_country.data,
                'phone': form.phone.data,
                'email': form.email.data,
                'next_of_kin': form.next_of_kin.data,
                'next_of_kin_relation': form.next_of_kin_relation.data,
                'next_of_kin_phone': form.next_of_kin_phone.data
            }
            return redirect(url_for('citizen.upload_passport'))
        
        return render_template('citizen/passport-application.html', form=form)

    @bp.route('/pancard-application', methods=['GET', 'POST'])
    @login_required
    def pancard_application():
        if not check_citizen_access():
            flash('Access denied. You must be logged in as a citizen.', 'danger')
            return redirect(url_for('main.index'))
        
        form = PanCardApplicationForm()
        if form.validate_on_submit():
            # Store form data in session
            session['pancard_application_data'] = {
                'full_name': form.full_name.data,
                'father_name': form.father_name.data,
                'date_of_birth': form.date_of_birth.data.strftime('%Y-%m-%d') if form.date_of_birth.data else None,
                'gender': form.gender.data,
                'permanent_address': form.permanent_address.data,
                'permanent_state': form.permanent_state.data,
                'permanent_pincode': form.permanent_pincode.data,
                'permanent_country': form.permanent_country.data,
                'current_address': form.current_address.data,
                'current_state': form.current_state.data,
                'current_pincode': form.current_pincode.data,
                'current_country': form.current_country.data,
                'phone': form.phone.data,
                'email': form.email.data,
                'aadhaar_number': form.aadhaar_number.data
            }
            return redirect(url_for('citizen.upload_pancard'))
        
        return render_template('citizen/pancard-application.html', form=form)

    @bp.route('/upload-passport', methods=['GET', 'POST'])
    @login_required
    def upload_passport():
        if not check_citizen_access():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if application data exists in session
        if 'passport_application_data' not in session:
            flash('Please complete the application form first', 'warning')
            return redirect(url_for('citizen.passport_application'))
        
        form = PassportDocumentForm()
        if form.validate_on_submit():
            try:
                application_number = f"PASSPORT-{str(uuid.uuid4())[:8]}"
                application_data = session['passport_application_data']
                
                # Parse date string back to date object
                dob = datetime.strptime(application_data['date_of_birth'], '%Y-%m-%d')
                
                new_application = Application(
                    user_id=current_user.id,
                    document_type='passport',
                    application_number=application_number,
                    status='pending',
                    name=application_data['full_name'],
                    dob=dob,
                    gender=application_data['gender'],
                    # Fix the address field to use permanent and current addresses
                    address=application_data['permanent_address'] + " (Permanent)\n" + 
                            application_data['permanent_state'] + ", " + 
                            application_data['permanent_pincode'] + ", " + 
                            application_data['permanent_country'] + 
                            "\n\n" + 
                            application_data['current_address'] + " (Current)\n" + 
                            application_data['current_state'] + ", " + 
                            application_data['current_pincode'] + ", " + 
                            application_data['current_country'],
                    phone=application_data['phone'],
                    email=application_data['email'],
                    next_of_kin=application_data['next_of_kin'],
                    next_of_kin_relation=application_data['next_of_kin_relation'],
                    next_of_kin_phone=application_data['next_of_kin_phone']
                )
                
                db.session.add(new_application)
                db.session.flush()
                
                # Create a temporary directory for file processing
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save photo temporarily for PDF generation
                    photo_file = form.photo.data
                    photo_filename = secure_filename(photo_file.filename)
                    photo_path = os.path.join(temp_dir, photo_filename)
                    photo_file.save(photo_path)
                    
                    # Get the app instance for logging
                    app = current_app
                    
                    # Generate PDF application form with embedded photo
                    pdf_path = generate_application_pdf(
                        app,
                        application_data, 
                        photo_path, 
                        'passport', 
                        temp_dir
                    )
                    
                    if pdf_path:
                        # Upload PDF application form to Google Drive
                        pdf_drive_id = upload_to_drive(pdf_path, f"{application_number}_application_form.pdf", app)
                        
                        # Add application form as a document
                        application_form_doc = Document(
                            application_id=new_application.id,
                            document_type='application_form',
                            file_path=pdf_drive_id,
                            filename=f"{application_number}_application_form.pdf"
                        )
                        db.session.add(application_form_doc)
                        
                        # Add logging here after the document is created
                        app.logger.info(f"Created application form document with ID: {application_form_doc.id} and file path: {pdf_drive_id}")
                    
                    # Continue with existing file upload code...
                    files = {
                        'id_proof': form.id_proof.data,
                        'photo': form.photo.data,
                        'address_proof': form.address_proof.data,
                        'dob_proof': form.dob_proof.data
                    }
                    
                    for field_name, file in files.items():
                        if file and allowed_file(file.filename):
                            # Upload to Google Drive
                            result = upload_document_to_drive(file, application_number, field_name, temp_dir)
                            
                            # Check if result is a tuple (file_id, mime_type) or just file_id
                            if isinstance(result, tuple):
                                drive_file_id, mime_type = result
                            else:
                                drive_file_id = result
                                mime_type = None
                            
                            if drive_file_id:
                                new_document = Document(
                                    application_id=new_application.id,
                                    document_type=field_name,
                                    file_path=drive_file_id,
                                    filename=secure_filename(file.filename),
                                    mime_type=mime_type
                                )
                                db.session.add(new_document)
                                app.logger.info(f"Created {field_name} document with ID: {new_document.id} and MIME type: {mime_type}")
                            else:
                                app.logger.error(f"Failed to upload {field_name}")
                    
                # Clear session data after successful submission
                session.pop('passport_application_data', None)
                
                # Make sure to commit the session before returning
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Documents uploaded successfully',
                    'redirect': url_for('citizen.dashboard')
                })
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error in upload_passport: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        if request.method == 'GET':
            return render_template('citizen/upload-passport.html', form=form)
        
        return jsonify({'success': False, 'error': 'Invalid form data'}), 400

    @bp.route('/upload-pancard', methods=['GET', 'POST'])
    @login_required
    def upload_pancard():
        if not check_citizen_access():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if application data exists in session
        if 'pancard_application_data' not in session:
            flash('Please complete the application form first', 'warning')
            return redirect(url_for('citizen.pancard_application'))
        
        form = PanCardDocumentForm()
        if form.validate_on_submit():
            try:
                # Get the app instance for logging
                app = current_app
                app.logger.info("Starting PAN card document upload process")
                
                application_number = f"PANCARD-{str(uuid.uuid4())[:8]}"
                application_data = session['pancard_application_data']
                
                # Parse date string back to date object
                dob = datetime.strptime(application_data['date_of_birth'], '%Y-%m-%d')
                
                # Create the application object first
                new_application = Application(
                    user_id=current_user.id,
                    document_type='pancard',
                    application_number=application_number,
                    status='pending',
                    name=application_data['full_name'],
                    dob=dob,
                    gender=application_data['gender'],
                    address=application_data['permanent_address'] + " (Permanent)\n" + 
                            application_data['permanent_state'] + ", " + 
                            application_data['permanent_pincode'] + ", " + 
                            application_data['permanent_country'] + 
                            "\n\n" + 
                            application_data['current_address'] + " (Current)\n" + 
                            application_data['current_state'] + ", " + 
                            application_data['current_pincode'] + ", " + 
                            application_data['current_country'],
                    phone=application_data['phone'],
                    email=application_data['email'],
                    father_name=application_data.get('father_name', ''),
                    aadhaar_number=application_data.get('aadhaar_number', '')
                )
                
                db.session.add(new_application)
                db.session.flush()
                app.logger.info(f"Created new application with ID: {new_application.id}")
                
                # Create a temporary directory for file processing
                with tempfile.TemporaryDirectory() as temp_dir:
                    app.logger.info(f"Created temporary directory: {temp_dir}")
                    
                    # Save photo temporarily for PDF generation
                    photo_file = form.photo.data
                    if not photo_file:
                        app.logger.error("Photo file is missing")
                        raise ValueError("Photo file is required")
                        
                    photo_filename = secure_filename(photo_file.filename)
                    photo_path = os.path.join(temp_dir, photo_filename)
                    photo_file.save(photo_path)
                    app.logger.info(f"Saved photo to: {photo_path}")
                    
                    # Generate PDF application form with embedded photo
                    pdf_path = generate_application_pdf(
                        app,
                        application_data, 
                        photo_path, 
                        'pancard', 
                        temp_dir
                    )
                    
                    if not pdf_path:
                        app.logger.error("Failed to generate PDF")
                        raise ValueError("Failed to generate application PDF")
                    
                    app.logger.info(f"Generated PDF at: {pdf_path}")
                    
                    # Upload PDF application form to Google Drive
                    pdf_drive_id = upload_to_drive(pdf_path, f"{application_number}_application_form.pdf", app)
                    
                    if not pdf_drive_id:
                        app.logger.error("Failed to upload PDF to Drive")
                        raise ValueError("Failed to upload application PDF to Drive")
                    
                    app.logger.info(f"Uploaded PDF to Drive with ID: {pdf_drive_id}")
                    
                    # Add application form as a document
                    application_form_doc = Document(
                        application_id=new_application.id,
                        document_type='application_form',
                        file_path=pdf_drive_id,
                        filename=f"{application_number}_application_form.pdf"
                    )
                    db.session.add(application_form_doc)
                    app.logger.info(f"Created application form document with ID: {application_form_doc.id}")
                    
                    # Process other document uploads
                    files = {
                        'id_proof': form.id_proof.data,
                        'photo': form.photo.data,
                        'address_proof': form.address_proof.data,
                        'signature': form.signature.data
                    }
                    
                    # Track successful uploads
                    successful_uploads = 0
                    required_uploads = 0
                    
                    for field_name, file in files.items():
                        if file and allowed_file(file.filename):
                            required_uploads += 1
                            app.logger.info(f"Processing {field_name} file: {file.filename}")
                            
                            # Create a fresh file object to avoid issues with already-read files
                            if field_name == 'photo':
                                # For photo, we already saved it, so use the saved file
                                with open(photo_path, 'rb') as f:
                                    file_content = f.read()
                                
                                # Create a new FileStorage object
                                from werkzeug.datastructures import FileStorage
                                file = FileStorage(
                                    stream=io.BytesIO(file_content),
                                    filename=photo_filename,
                                    content_type='image/jpeg'
                                )
                            
                            # Upload to Google Drive with better error handling
                            try:
                                result = upload_document_to_drive(file, application_number, field_name, temp_dir)
                                
                                if result is None:
                                    app.logger.error(f"Failed to upload {field_name} to Drive")
                                    continue
                                    
                                # Check if result is a tuple (file_id, mime_type) or just file_id
                                if isinstance(result, tuple):
                                    drive_file_id, mime_type = result
                                else:
                                    drive_file_id = result
                                    mime_type = None
                                
                                # Create document record in database
                                new_document = Document(
                                    application_id=new_application.id,
                                    document_type=field_name,
                                    file_path=drive_file_id,
                                    filename=secure_filename(file.filename if file.filename else ''),
                                    mime_type=mime_type
                                )
                                db.session.add(new_document)
                                app.logger.info(f"Created {field_name} document with ID: {new_document.id}")
                                successful_uploads += 1
                            except Exception as e:
                                app.logger.error(f"Error processing {field_name}: {str(e)}")
                                # Continue with other files instead of failing the whole process
                    
                    # Check if all required uploads were successful
                    if successful_uploads < required_uploads:
                        app.logger.warning(f"Not all documents were uploaded successfully: {successful_uploads}/{required_uploads}")
                    
                    # Clear session data after successful submission
                    session.pop('pancard_application_data', None)
                    
                    # Commit all changes to the database
                    db.session.commit()
                    app.logger.info("Successfully completed PAN card application submission")
                    
                    return jsonify({
                        'success': True,
                        'message': 'Documents uploaded successfully',
                        'redirect': url_for('citizen.dashboard')
                    })
                    
            except Exception as e:
                db.session.rollback()
                app = current_app
                app.logger.error(f"Error in upload_pancard: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        if request.method == 'GET':
            return render_template('citizen/upload-pancard.html', form=form)
        
        return jsonify({'success': False, 'error': 'Invalid form data'}), 400
    
    return bp