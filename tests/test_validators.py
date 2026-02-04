"""Test validators."""
import pytest
from app.utils.validators import validate_google_drive_url, validate_file_extension


class TestGoogleDriveURLValidator:
    """Test Google Drive URL validation."""

    def test_valid_folder_url(self):
        """Test valid folder URL."""
        url = "https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j"
        is_valid, resource_type, resource_id, error = validate_google_drive_url(url)

        assert is_valid is True
        assert resource_type == 'folder'
        assert resource_id == '1a2b3c4d5e6f7g8h9i0j'
        assert error is None

    def test_valid_file_url(self):
        """Test valid file URL."""
        url = "https://drive.google.com/file/d/1a2b3c4d5e6f7g8h9i0j/view"
        is_valid, resource_type, resource_id, error = validate_google_drive_url(url)

        assert is_valid is True
        assert resource_type == 'file'
        assert resource_id == '1a2b3c4d5e6f7g8h9i0j'
        assert error is None

    def test_invalid_url_format(self):
        """Test invalid URL format."""
        url = "not a valid url"
        is_valid, resource_type, resource_id, error = validate_google_drive_url(url)

        assert is_valid is False
        assert error is not None

    def test_non_drive_url(self):
        """Test non-Google Drive URL."""
        url = "https://example.com/some/path"
        is_valid, resource_type, resource_id, error = validate_google_drive_url(url)

        assert is_valid is False
        assert error == "URL must be from Google Drive"

    def test_empty_url(self):
        """Test empty URL."""
        url = ""
        is_valid, resource_type, resource_id, error = validate_google_drive_url(url)

        assert is_valid is False
        assert error == "URL is required"

    def test_none_url(self):
        """Test None URL."""
        url = None
        is_valid, resource_type, resource_id, error = validate_google_drive_url(url)

        assert is_valid is False
        assert error == "URL is required"


class TestFileExtensionValidator:
    """Test file extension validation."""

    def test_valid_pdf_extension(self):
        """Test valid PDF extension."""
        filename = "invoice.pdf"
        allowed = {'pdf'}

        assert validate_file_extension(filename, allowed) is True

    def test_valid_pdf_uppercase(self):
        """Test valid PDF extension with uppercase."""
        filename = "invoice.PDF"
        allowed = {'pdf'}

        assert validate_file_extension(filename, allowed) is True

    def test_invalid_extension(self):
        """Test invalid extension."""
        filename = "document.docx"
        allowed = {'pdf'}

        assert validate_file_extension(filename, allowed) is False

    def test_no_extension(self):
        """Test filename without extension."""
        filename = "invoice"
        allowed = {'pdf'}

        assert validate_file_extension(filename, allowed) is False

    def test_empty_filename(self):
        """Test empty filename."""
        filename = ""
        allowed = {'pdf'}

        assert validate_file_extension(filename, allowed) is False

    def test_multiple_allowed_extensions(self):
        """Test multiple allowed extensions."""
        allowed = {'pdf', 'png', 'jpg'}

        assert validate_file_extension("file.pdf", allowed) is True
        assert validate_file_extension("file.png", allowed) is True
        assert validate_file_extension("file.jpg", allowed) is True
        assert validate_file_extension("file.docx", allowed) is False
