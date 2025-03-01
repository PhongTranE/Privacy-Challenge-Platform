"""
Test cases for File Upload and Extraction API:
    1. Test Successful ZIP File Upload
    2. Test Upload with Invalid File Type
    3. Test Upload Without a File
    4. Test ZIP Extraction with a Valid File
    5. Test ZIP Extraction with Multiple Files in ZIP (Should Fail)
"""
import logging
import io
import zipfile
import pytest
from http import HTTPStatus

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

UPLOAD_ENDPOINT = "/api/admin/upload"

@pytest.mark.usefixtures("client")
class TestFileUploadAPI:
    """Test class for File Upload API in Flask."""

    @pytest.fixture
    def zip_file(self):
        """Create a mock ZIP file containing a single CSV file."""
        zip_stream = io.BytesIO()
        with zipfile.ZipFile(zip_stream, "w") as zipf:
            zipf.writestr("data.csv", "id,name\n1,Test")
        zip_stream.seek(0)
        return zip_stream
    
    @pytest.fixture
    def invalid_zip_file(self):
        """Create a mock ZIP file containing multiple files (should fail extraction)."""
        zip_stream = io.BytesIO()
        with zipfile.ZipFile(zip_stream, "w") as zipf:
            zipf.writestr("data1.csv", "id,name\n1,Test")
            zipf.writestr("data2.csv", "id,name\n2,Another")
        zip_stream.seek(0)
        return zip_stream
    
    @pytest.fixture
    def non_zip_file(self):
        """Create a mock invalid file (e.g., .txt instead of .zip)."""
        return io.BytesIO(b"Hello, this is a test text file.")

    @pytest.fixture
    def large_zip_file(self):
        """Create a ZIP file exceeding the size limit."""
        zip_stream = io.BytesIO()
        with zipfile.ZipFile(zip_stream, "w") as zipf:
            zipf.writestr("large_file.csv", "A" * (60 * 1024 * 1024))  # 60MB file (exceeds 50MB limit)
        zip_stream.seek(0)
        return zip_stream

    # --------------------------
    # TEST CASES FOR UPLOADING FILES
    # --------------------------

    def test_successful_zip_upload(self, client, zip_file):
        """Test uploading a valid ZIP file."""
        response = client.post(UPLOAD_ENDPOINT, data={"file": (zip_file, "test.zip")}, content_type="multipart/form-data")

        assert response.status_code == HTTPStatus.CREATED
        assert "file_path" in response.json
        assert "extracted_file_path" in response.json

    def test_invalid_file_type_upload(self, client, non_zip_file):
        """Test uploading an invalid file type."""
        response = client.post(UPLOAD_ENDPOINT, data={"file": (non_zip_file, "test.txt")}, content_type="multipart/form-data")
        
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Invalid file type" in response.json["message"]

    def test_upload_without_file(self, client):
        """Test making a request without an uploaded file."""
        response = client.post(UPLOAD_ENDPOINT, data={}, content_type="multipart/form-data")
        
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "No file uploaded" in response.json["message"]

    def test_upload_large_file(self, client, large_zip_file):
        """Test uploading a ZIP file larger than the allowed limit."""
        response = client.post(UPLOAD_ENDPOINT, data={"file": (large_zip_file, "large.zip")}, content_type="multipart/form-data")
        
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Zip file too big" in response.json["message"]

    # --------------------------
    # TEST CASES FOR FILE EXTRACTION
    # --------------------------

    def test_zip_extraction_multiple_files(self, client, invalid_zip_file):
        """Test extraction should fail when ZIP contains multiple files."""
        response = client.post(UPLOAD_ENDPOINT, data={"file": (invalid_zip_file, "invalid.zip")}, content_type="multipart/form-data")

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "ZIP file must contain exactly one file!" in response.json["message"]
