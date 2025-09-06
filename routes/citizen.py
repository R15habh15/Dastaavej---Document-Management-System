from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, jsonify, session
import os
import uuid
from datetime import datetime
import time
import tempfile
from werkzeug.utils import secure_filename
from models import User, Application, Document, StatusUpdate, Notification
from extensions import db
from forms import (
    UploadDocumentForm, PassportApplicationForm, PassportDocumentForm, 
    PanCardApplicationForm, PanCardDocumentForm
)
from flask_login import login_required, current_user
from drive_api import upload_to_drive, download_from_drive, get_drive_preview_url
from utils import generate_application_pdf
from .citizen_helpers import check_citizen_access, allowed_file, upload_document_to_drive, get_document_preview, get_application_documents

citizen_bp = Blueprint('citizen', __name__)

@citizen_bp.route('/dashboard')
@login_required
def dashboard():
    """Display the citizen dashboard"""
    if not check_citizen_access():
        return redirect(url_for('main.index'))
    
    # Get only the most recent application for each document type
    recent_applications = {}
    
    # Get all applications for the current user
    all_applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.created_at.desc()).all()
    
    # Group by document type and keep only the most recent
    for application in all_applications:
        doc_type = application.document_type
        if doc_type not in recent_applications:
            recent_applications[doc_type] = application
    
    # Convert dictionary to list for the template
    applications = list(recent_applications.values())
    
    return render_template('citizen/dashboard.html', applications=applications)

@citizen_bp.route('/application-status/<int:application_id>')
@login_required
def application_status(application_id):
    if not check_citizen_access():
        return redirect(url_for('main.index'))
    
    application = Application.query.get_or_404(application_id)
    
    if application.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('citizen.dashboard'))
    
    # Fix: Use query instead of directly accessing the relationship
    status_updates = StatusUpdate.query.filter_by(application_id=application_id).order_by(StatusUpdate.updated_at.desc()).all()
    
    return render_template('citizen/application-status.html', 
                          application=application, 
                          status_updates=status_updates,
                          get_application_documents=get_application_documents)

# Import the document routes
from .citizen_documents import register_document_routes
register_document_routes(citizen_bp)

# Import the application routes
from .citizen_applications import register_application_routes
register_application_routes(citizen_bp)

@citizen_bp.route('/notifications')
@login_required
def notifications():
    if not check_citizen_access():
        return redirect(url_for('main.index'))
    
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark all notifications as read
    for notification in notifications:
        if not notification.is_read:
            notification.is_read = True
            db.session.commit()
    
    return render_template('citizen/notifications.html', notifications=notifications)


# Add the missing view_applications route
@citizen_bp.route('/view-applications')
@login_required
def view_applications():
    """View all applications for the current user"""
    if not check_citizen_access():
        return redirect(url_for('main.index'))
    
    # Get all applications for the current user
    applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.created_at.desc()).all()
    
    return render_template('citizen/view_applications.html', applications=applications)