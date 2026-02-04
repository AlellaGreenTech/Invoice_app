"""Input validation utilities."""
import re
import validators


def validate_google_drive_url(url):
    """
    Validate Google Drive URL and extract folder/file ID.

    Args:
        url: Google Drive URL string

    Returns:
        tuple: (is_valid, resource_type, resource_id, error_message)
    """
    if not url or not isinstance(url, str):
        return False, None, None, "URL is required"

    # Validate URL format
    if not validators.url(url):
        return False, None, None, "Invalid URL format"

    # Check if it's a Google Drive URL
    if 'drive.google.com' not in url:
        return False, None, None, "URL must be from Google Drive"

    # Extract folder ID
    folder_match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url)
    if folder_match:
        return True, 'folder', folder_match.group(1), None

    # Extract file ID
    file_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if file_match:
        return True, 'file', file_match.group(1), None

    # Try to extract ID from other formats
    id_match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if id_match:
        return True, 'unknown', id_match.group(1), None

    return False, None, None, "Could not extract resource ID from URL"


def validate_file_extension(filename, allowed_extensions):
    """
    Validate file extension.

    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions

    Returns:
        bool: True if extension is allowed
    """
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
