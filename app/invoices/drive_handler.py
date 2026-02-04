"""Google Drive handler for accessing and downloading files."""
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from flask import current_app
from app.auth.google_auth import GoogleAuth
from app.utils.validators import validate_google_drive_url, validate_file_extension


class DriveHandler:
    """Handler for Google Drive operations."""

    def __init__(self, user):
        """
        Initialize Drive handler with user credentials.

        Args:
            user: User model instance with OAuth tokens
        """
        self.user = user
        self.credentials = GoogleAuth.get_credentials_from_user(user)
        self.service = build('drive', 'v3', credentials=self.credentials)

    def list_files_in_folder(self, folder_id):
        """
        List all PDF files in a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            list: List of file dictionaries with id, name, mimeType, size
        """
        try:
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"

            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime)",
                pageSize=1000
            ).execute()

            files = results.get('files', [])

            current_app.logger.info(f'Found {len(files)} PDF files in folder {folder_id}')

            return files

        except HttpError as error:
            current_app.logger.error(f'Drive API error: {error}')
            if error.resp.status == 404:
                raise ValueError('Folder not found or not accessible')
            elif error.resp.status == 403:
                raise ValueError('Access denied. Please ensure the folder is shared with your account.')
            else:
                raise ValueError(f'Failed to access Google Drive: {error}')

    def get_file_metadata(self, file_id):
        """
        Get metadata for a specific file.

        Args:
            file_id: Google Drive file ID

        Returns:
            dict: File metadata
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime"
            ).execute()

            return file

        except HttpError as error:
            current_app.logger.error(f'Failed to get file metadata: {error}')
            raise ValueError(f'Failed to access file: {error}')

    def download_file(self, file_id, destination_path):
        """
        Download a file from Google Drive.

        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save the file

        Returns:
            str: Path to downloaded file
        """
        try:
            request = self.service.files().get_media(fileId=file_id)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            # Download file
            with io.FileIO(destination_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        current_app.logger.debug(f'Download progress: {int(status.progress() * 100)}%')

            current_app.logger.info(f'Downloaded file {file_id} to {destination_path}')

            return destination_path

        except HttpError as error:
            current_app.logger.error(f'Failed to download file: {error}')
            raise ValueError(f'Failed to download file: {error}')

    def download_file_to_memory(self, file_id):
        """
        Download a file to memory (BytesIO).

        Args:
            file_id: Google Drive file ID

        Returns:
            io.BytesIO: File content in memory
        """
        try:
            request = self.service.files().get_media(fileId=file_id)

            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            file_content.seek(0)
            return file_content

        except HttpError as error:
            current_app.logger.error(f'Failed to download file to memory: {error}')
            raise ValueError(f'Failed to download file: {error}')

    def validate_folder_access(self, folder_id):
        """
        Validate that the user has access to the folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            bool: True if accessible, raises ValueError otherwise
        """
        try:
            folder = self.service.files().get(
                fileId=folder_id,
                fields="id, name, mimeType"
            ).execute()

            if folder.get('mimeType') != 'application/vnd.google-apps.folder':
                raise ValueError('The provided ID is not a folder')

            return True

        except HttpError as error:
            if error.resp.status == 404:
                raise ValueError('Folder not found')
            elif error.resp.status == 403:
                raise ValueError('Access denied to folder')
            else:
                raise ValueError(f'Failed to validate folder access: {error}')

    @staticmethod
    def parse_drive_url(url):
        """
        Parse Google Drive URL and extract resource information.

        Args:
            url: Google Drive URL

        Returns:
            dict: {
                'is_valid': bool,
                'resource_type': str ('folder' or 'file'),
                'resource_id': str,
                'error': str or None
            }
        """
        is_valid, resource_type, resource_id, error = validate_google_drive_url(url)

        return {
            'is_valid': is_valid,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'error': error
        }

    def process_drive_url(self, drive_url):
        """
        Process a Drive URL and return list of PDF files.

        Args:
            drive_url: Google Drive folder or file URL

        Returns:
            list: List of file dictionaries

        Raises:
            ValueError: If URL is invalid or inaccessible
        """
        # Parse URL
        parsed = self.parse_drive_url(drive_url)

        if not parsed['is_valid']:
            raise ValueError(parsed['error'])

        resource_id = parsed['resource_id']
        resource_type = parsed['resource_type']

        # Handle folder
        if resource_type == 'folder':
            self.validate_folder_access(resource_id)
            return self.list_files_in_folder(resource_id)

        # Handle single file
        elif resource_type == 'file':
            file_metadata = self.get_file_metadata(resource_id)

            # Validate it's a PDF
            if file_metadata.get('mimeType') != 'application/pdf':
                raise ValueError('File must be a PDF')

            return [file_metadata]

        else:
            # Try as folder first, then as file
            try:
                self.validate_folder_access(resource_id)
                return self.list_files_in_folder(resource_id)
            except ValueError:
                try:
                    file_metadata = self.get_file_metadata(resource_id)
                    if file_metadata.get('mimeType') != 'application/pdf':
                        raise ValueError('File must be a PDF')
                    return [file_metadata]
                except ValueError:
                    raise ValueError('Could not access resource as folder or file')
