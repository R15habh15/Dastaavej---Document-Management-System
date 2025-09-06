from flask import current_app, flash, redirect, url_for
from flask_login import current_user
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
from models import Document
from drive_api import upload_to_drive, download_from_drive, get_drive_preview_url

def check_citizen_access():
    """Check if the current user has citizen access"""
    if current_user.role != 'citizen':
        flash('Access denied', 'danger')
        return False
    return True

def allowed_file(filename):
    """Check if a file extension is allowed."""
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'jpg', 'jpeg', 'png'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def upload_document_to_drive(file, application_number, field_name, temp_dir=None):
    """Upload a document to Google Drive and return the file ID and mime type"""
    app = current_app
    
    if not file or not allowed_file(file.filename):
        app.logger.error(f"Invalid file or file type: {file.filename if file else 'None'}")
        return None
        
    filename = secure_filename(file.filename)
    
    # Determine MIME type based on file extension
    mime_type = None
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
        if ext == 'pdf':
            mime_type = 'application/pdf'
        elif ext in ['jpg', 'jpeg']:
            mime_type = 'image/jpeg'
        elif ext == 'png':
            mime_type = 'image/png'
    
    # Create a temporary directory if not provided
    created_temp_dir = False
    if not temp_dir:
        temp_dir = tempfile.mkdtemp()
        created_temp_dir = True
    
    temp_path = None
    try:
        # Save the file temporarily
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        app.logger.info(f"Saved {field_name} file temporarily at: {temp_path}")
        
        # Upload to Google Drive
        drive_file_id = upload_to_drive(temp_path, f"{application_number}_{field_name}_{filename}", app)
        
        if not drive_file_id:
            app.logger.error(f"Failed to upload {field_name} to Google Drive")
            return None
            
        app.logger.info(f"Successfully uploaded {field_name} to Drive with ID: {drive_file_id}")
        
        # Return both the file ID and MIME type as a tuple
        return (drive_file_id, mime_type)
        
    except Exception as e:
        app.logger.error(f"Error in upload_document_to_drive for {field_name}: {str(e)}")
        return None
        
    finally:
        # Clean up if we created our own temp directory
        if created_temp_dir and temp_dir and os.path.exists(temp_dir):
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                os.rmdir(temp_dir)
            except Exception as e:
                app.logger.error(f"Error cleaning up temp files: {str(e)}")

def get_document_preview(document):
    """Get a preview URL for a document"""
    if not document:
        return None
        
    # Get the preview URL
    preview_url = get_drive_preview_url(document.file_path)
    return preview_url

def get_application_documents(application_id):
    """Get all documents for an application grouped by type"""
    documents = Document.query.filter_by(application_id=application_id).all()
    
    # Group documents by type
    document_groups = {}
    
    for doc in documents:
        if doc.document_type != 'application_form':  # Skip application form as it has its own buttons
            # Format the document type for display
            display_name = doc.document_type.replace('_', ' ').title()
            
            document_groups[doc.document_type] = {
                'id': doc.id,
                'display_name': display_name,
                'file_path': doc.file_path,
                'document_type': doc.document_type
            }
    
    return document_groups

def generate_application_pdf(app, application_data, photo_path, document_type, temp_dir):
    """Generate a PDF application form with embedded photo"""
    try:
        app.logger.info(f"Generating PDF for {document_type} application")
        app.logger.info(f"Photo path: {photo_path}, exists: {os.path.exists(photo_path)}")
        
        # Create a unique filename for the PDF
        pdf_filename = f"{document_type}_application_{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        app.logger.info(f"PDF will be saved to: {pdf_path}")
        
        # Create PDF using ReportLab
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
        # Create the PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create content elements
        elements = []
        
        # Add title
        title_style = styles['Heading1']
        title_style.alignment = 1  # Center alignment
        title = Paragraph(f"{document_type.upper()} APPLICATION FORM", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Add photo if it exists
        if os.path.exists(photo_path):
            app.logger.info(f"Adding photo from {photo_path}")
            img = Image(photo_path, width=100, height=120)
            elements.append(img)
            elements.append(Spacer(1, 10))
        else:
            app.logger.warning(f"Photo not found at path: {photo_path}")
        
        # Add application data
        for key, value in application_data.items():
            if key != 'csrf_token':
                elements.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", styles['Normal']))
                elements.append(Spacer(1, 5))
        
        # Build the PDF
        doc.build(elements)
        
        # Verify the PDF was created
        if os.path.exists(pdf_path):
            app.logger.info(f"PDF successfully generated at: {pdf_path}")
            return pdf_path
        else:
            app.logger.error(f"PDF file not found at expected path: {pdf_path}")
            return None
            
    except Exception as e:
        app.logger.error(f"Error generating PDF: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return None