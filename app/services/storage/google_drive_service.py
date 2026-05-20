import os
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config.settings import settings
from app.infrastructure.logging.logger import get_logger
from app.services.storage.models import DriveUploadResult

logger = get_logger("google_drive")

SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveService:
    def __init__(self):
        self.service = self._get_drive_service()
    
    def _get_drive_service(self):
        """Authenticate and return Google Drive service"""
        creds = None
        token_path = settings.google_drive_token_path
        
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.google_oauth_credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('drive', 'v3', credentials=creds)
    
    def upload_file(
        self, 
        file_path: str, 
        folder_id: str | None = None
    ) -> DriveUploadResult:
        """Upload file to Google Drive and return shareable links"""
        file_path_obj = Path(file_path)
        folder_id = folder_id or settings.google_drive_folder_id
        
        if not folder_id:
            raise ValueError("Google Drive folder ID not configured")
        
        logger.info(f"Uploading {file_path_obj.name} to Google Drive")
        
        file_metadata = {
            'name': file_path_obj.name,
            'parents': [folder_id]
        }
        
        mime_type = 'video/mp4' if file_path_obj.suffix == '.mp4' else 'application/octet-stream'
        
        media = MediaFileUpload(
            str(file_path_obj), 
            mimetype=mime_type,
            resumable=True
        )
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, webContentLink, thumbnailLink'
        ).execute()
        
        self.service.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        logger.info(f"Uploaded successfully: {file['id']}")
        
        return DriveUploadResult(
            file_id=file['id'],
            file_name=file['name'],
            view_link=file['webViewLink'],
            download_link=file['webContentLink'],
            thumbnail_link=file.get('thumbnailLink')
        )
    
    def delete_file(self, file_id: str) -> None:
        """Delete file from Google Drive"""
        self.service.files().delete(fileId=file_id).execute()
        logger.info(f"Deleted file: {file_id}")
