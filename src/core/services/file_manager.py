import os
from werkzeug.utils import secure_filename
import uuid
import zipfile
import shutil
import tempfile
from flask import current_app

class FileManager:
    def __init__(self, upload_dir="default", allowed_extensions=None, max_zip_size=50_000_000):
        """
        Initializes the FileManager with a specified upload directory and allowed file types.
        - `upload_dir`: Directory where files will be stored.
        - `allowed_extensions`: Set of allowed file extensions.
        - `max_zip_size`: Maximum allowed size for ZIP files (default: 50MB).
        """
        self.test_mode = current_app.config.get("TESTING", False)

        # Determine src
        if self.test_mode:
            project_root = tempfile.gettempdir() 
        else:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        
        # Ensure the `uploads/` directory exists at the project root
        uploads_dir = os.path.join(project_root, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        # Store files inside `uploads/default` or a custom directory
        self.upload_dir = os.path.join(uploads_dir, upload_dir)
        os.makedirs(self.upload_dir, exist_ok=True)

        self.allowed_extensions = allowed_extensions or {"zip"}
        self.max_zip_size = max_zip_size

    def is_allowed_filename(self, filename):
        """Check if the file has an allowed extension."""
        return "." in filename and filename.rsplit(".", 1)[1].lower() in self.allowed_extensions

    def get_file_path(self, filename):
        return os.path.join(self.upload_dir, filename)
        
    def save_file(self, file, filename=None):
        filename = filename or secure_filename(file.filename)

        if not self.is_allowed_filename(filename) or not self.is_allowed_filename(file.filename):
            raise ValueError(f"Invalid file type: Allowed types: {self.allowed_extensions}")

        if not filename:
            unique_id = uuid.uuid4().hex[:16]
            # filename = f"{unique_id}_{filename}"
            extension = os.path.splitext(filename)[1].lower()  # Extract the extension
            filename = f"{unique_id}{extension}"

        file_path = os.path.abspath(os.path.join(self.upload_dir, filename))

        # Prevents malicious paths like ../../../etc/passwd.
        if not file_path.startswith(os.path.abspath(self.upload_dir)):
            raise ValueError("Invalid file path detected!")

        file.save(file_path)
        return file_path

    def is_safe_path(self, base_path, path):
        """Ensure the extracted file stays inside the allowed directory (Prevents Zip Slip)."""
        abs_base = os.path.abspath(base_path)
        abs_target = os.path.abspath(os.path.join(base_path, path))
        return abs_target.startswith(abs_base)
    
    
    def unzip_file(self, file_path):
        """Extracts a ZIP file containing exactly one file into the upload directory."""
        # Extract only the filename from the provided path
        filename = os.path.basename(file_path)
        safe_filename = secure_filename(filename)

        if not safe_filename.lower().endswith(".zip"):
            raise ValueError("Only .zip files can be unzipped!")

        zip_file_path = file_path  

        if not os.path.exists(zip_file_path):
            raise FileNotFoundError(f"File {zip_file_path} not found!")

        # Create a temporary extraction directory
        extraction_dir = os.path.join(self.upload_dir, f"{safe_filename}_extract")

        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                # Check total extracted size (Zip Bomb Protection)
                total_size = sum(f.file_size for f in zip_ref.infolist())
                if total_size > self.max_zip_size:
                    raise ValueError("Zip file too big (possible Zip Bomb attack).")

                # Extract files to a temporary directory
                os.makedirs(extraction_dir, exist_ok=True)
                zip_ref.extractall(extraction_dir)

                # List extracted files
                extracted_files = os.listdir(extraction_dir)
                if len(extracted_files) != 1:
                    raise ValueError("ZIP file must contain exactly one file!")

                # Ensure the extracted file is a CSV
                extracted_file = extracted_files[0]
                extracted_extension = os.path.splitext(extracted_file)[1].lower()
                if extracted_extension != ".csv":
                    raise ValueError("Only .csv files are allowed in the ZIP!")

                # Move the extracted CSV file to the upload directory
                extracted_file_path = os.path.join(extraction_dir, extracted_file)
                final_file_path = os.path.join(self.upload_dir, extracted_file)

                os.rename(extracted_file_path, final_file_path)
                return final_file_path

        finally:
            if os.path.exists(extraction_dir):
                shutil.rmtree(extraction_dir)

    def delete_file(self, filename):
        """Deletes a file from the upload directory, raising an exception if it doesn't exist."""
        file_path = os.path.join(self.upload_dir, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{filename}' not found.")

        try:
            os.remove(file_path)
        except OSError as e:
            raise RuntimeError(f"Failed to delete '{filename}': {e}")

        return f"File '{filename}' deleted successfully."


