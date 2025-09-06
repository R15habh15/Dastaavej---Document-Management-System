import os
import mimetypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.http import MediaIoBaseDownload
from config import Config

# Load Google Drive API credentials
try:
    if not os.path.exists(Config.GOOGLE_DRIVE_CREDENTIALS):
        raise FileNotFoundError(f"Credentials file not found at {Config.GOOGLE_DRIVE_CREDENTIALS}")
        
    credentials = Credentials.from_service_account_file(
        Config.GOOGLE_DRIVE_CREDENTIALS, 
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    drive_service = build("drive", "v3", credentials=credentials)
    print("Google Drive API initialized successfully")
except Exception as e:
    print(f"Failed to initialize Google Drive API: {str(e)}")
    drive_service = None

# Define the fixed folder ID for "Dastaavej Uploads"
FOLDER_ID = "1RelKng-XcPvST4W02147Rr0R3YNaqtVe"

def get_drive_service():
    """Get the Google Drive service object"""
    return drive_service

def get_folder_id():
    """Get the folder ID for uploads"""
    return FOLDER_ID

def upload_to_drive(file_path, file_name, app=None):
    """Upload a file to Google Drive and return the file ID"""
    try:
        if app:
            app.logger.info(f"Uploading {file_path} to Google Drive as {file_name}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            if app:
                app.logger.error(f"File not found at path: {file_path}")
            return None
        
        # Get Drive service
        service = get_drive_service()
        if not service:
            if app:
                app.logger.error("Failed to get Drive service")
            return None
        
        # File metadata
        file_metadata = {
            'name': file_name,
            'parents': [get_folder_id()]
        }
        
        # Determine MIME type
        mime_type = mimetypes.guess_type(file_path)[0]
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        if app:
            app.logger.info(f"Detected MIME type: {mime_type}")
        
        # Create media
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        
        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        
        if app:
            app.logger.info(f"Successfully uploaded to Drive with ID: {file_id}")
        
        # Set permissions to anyone with the link can view
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'},
            fields='id'
        ).execute()
        
        return file_id
        
    except Exception as e:
        if app:
            app.logger.error(f"Error uploading to Drive: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
        return None

def download_from_drive(file_id, destination_path):
    """Downloads a file from Google Drive by its ID and saves it to the specified path."""
    try:
        if not drive_service:
            raise RuntimeError("Google Drive service not initialized")
            
        # Ensure the file_id is valid
        if not file_id or len(file_id) < 10:
            raise ValueError("Invalid Google Drive file ID")
            
        print(f"Attempting to download file ID: {file_id}")
        
        request = drive_service.files().get_media(fileId=file_id)
        
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        with open(destination_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download progress: {int(status.progress() * 100)}%")
        
        print(f"Successfully downloaded file to: {destination_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading file from Google Drive: {str(e)}")
        import traceback
        print(traceback.format_exc())
        if os.path.exists(destination_path):
            os.remove(destination_path)
        return False

def get_drive_preview_url(file_id):
    """Get a preview URL for a Google Drive file"""
    try:
        if not file_id:
            return None
            
        if not drive_service:
            return None
        file = drive_service.files().get(
            fileId=file_id,
            fields='webViewLink'
        ).execute()
        
        return file.get('webViewLink')
        
    except Exception as e:
        print(f"Error getting preview URL: {str(e)}")
        return None

def get_direct_image_url(file_id):
    """Get a direct URL for viewing an image from Google Drive"""
    if not file_id:
        return None
    
    try:
        # First verify the file exists and get its metadata
        if not drive_service:
            return None
        file = drive_service.files().get(
            fileId=file_id,
            fields='id,mimeType'
        ).execute()
        
        # Create a publicly accessible link
        try:
            if drive_service:
                drive_service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'},
                fields='id'
            ).execute()
        except Exception as e:
            print(f"Error setting permissions (may already be public): {str(e)}")
        
        # Return a direct download link that works for images
        return f"https://drive.google.com/uc?id={file_id}"
    except Exception as e:
        print(f"Error creating direct image URL: {str(e)}")
        return None