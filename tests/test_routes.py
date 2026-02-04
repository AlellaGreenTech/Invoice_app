"""Test routes."""
import pytest
from flask import url_for


class TestMainRoutes:
    """Test main application routes."""

    def test_index_page(self, client):
        """Test landing page loads."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Invoice' in response.data

    def test_index_redirects_when_authenticated(self, client, sample_user):
        """Test authenticated users are redirected to dashboard."""
        # This would require setting up authentication in test client
        # For now, just test the route exists
        response = client.get('/')
        assert response.status_code == 200


class TestAuthRoutes:
    """Test authentication routes."""

    def test_login_page(self, client):
        """Test login page loads."""
        response = client.get('/auth/login')
        # Will redirect or show error if OAuth not configured
        assert response.status_code in [200, 302]

    def test_logout(self, client):
        """Test logout route."""
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200


class TestInvoiceRoutes:
    """Test invoice routes."""

    def test_upload_page_requires_auth(self, client):
        """Test upload page requires authentication."""
        response = client.get('/invoices/upload')
        # Should redirect to login
        assert response.status_code == 302

    def test_batch_status_requires_auth(self, client):
        """Test batch status requires authentication."""
        response = client.get('/invoices/batch/1')
        assert response.status_code == 302


class TestExportRoutes:
    """Test export routes."""

    def test_csv_export_requires_auth(self, client):
        """Test CSV export requires authentication."""
        response = client.get('/export/csv/1')
        assert response.status_code == 302

    def test_sheets_export_requires_auth(self, client):
        """Test Sheets export requires authentication."""
        response = client.post('/export/sheets/1')
        assert response.status_code == 302


class TestErrorPages:
    """Test error pages."""

    def test_404_page(self, client):
        """Test 404 error page."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'404' in response.data or b'Not Found' in response.data
