from flask import Blueprint, render_template
from extensions import db  # ✅ Fix: Import db from extensions.py

error_bp = Blueprint('error', __name__)

@error_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('error/error-404.html'), 404

@error_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()  # ✅ Fix: No circular import issue now
    return render_template('error/error-500.html'), 500
