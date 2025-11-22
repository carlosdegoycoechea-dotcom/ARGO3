"""
ARGO - Google Drive Synchronization
Automatic sync between Google Drive folder and local library cache
"""
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

from core.config import get_config
from core.logger import get_logger

logger = get_logger("GoogleDriveSync")


class GoogleDriveSync:
    """
    Synchronize Google Drive folder with local library cache
    
    Features:
    - Auto-detect changes (hash-based)
    - Download new/modified files
    - Categorize by Drive subfolder structure
    - Register in unified database
    - Incremental sync (only changed files)
    """
    
    def __init__(self, db_manager, config):
        """
        Initialize Drive sync
        
        Args:
            db_manager: UnifiedDatabase instance
            config: Configuration object
        """
        self.db = db_manager
        self.config = config
        self.service = None
        
        # Get paths
        self.cache_path = Path(config.get("paths.library_cache"))
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Get Drive folder ID
        self.library_folder_id = config.get("apis.google_drive.library_folder_id")
        
        if not self.library_folder_id:
            logger.warning("No LIBRARY_DRIVE_FOLDER_ID configured")
            return
        
        # Initialize Drive service
        self._init_drive_service()
    
    def _init_drive_service(self):
        """Initialize Google Drive API service"""
        creds_file = self.config.get("apis.google_drive.credentials_file")
        
        if not creds_file or not Path(creds_file).exists():
            logger.warning(f"Google credentials not found: {creds_file}")
            return
        
        try:
            # Use service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                creds_file,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {e}")
            self.service = None
    
    def is_available(self) -> bool:
        """Check if Drive sync is available"""
        return (
            self.service is not None and 
            self.library_folder_id is not None
        )
    
    def sync_library(self, force: bool = False) -> Dict[str, Any]:
        """
        Sync library from Google Drive
        
        Args:
            force: Force re-download all files
        
        Returns:
            Dict with sync statistics
        """
        if not self.is_available():
            logger.warning("Drive sync not available")
            return {
                "status": "unavailable",
                "error": "Drive not configured"
            }
        
        logger.info(f"Starting library sync (force={force})")
        
        stats = {
            "status": "success",
            "started_at": datetime.now().isoformat(),
            "files_scanned": 0,
            "files_downloaded": 0,
            "files_updated": 0,
            "files_skipped": 0,
            "errors": 0,
            "categories": {}
        }
        
        try:
            # List all files in Drive folder (recursive)
            drive_files = self._list_drive_files_recursive(self.library_folder_id)
            stats["files_scanned"] = len(drive_files)
            
            logger.info(f"Found {len(drive_files)} files in Drive")
            
            # Process each file
            for drive_file in drive_files:
                try:
                    result = self._sync_file(drive_file, force)
                    
                    if result["action"] == "downloaded":
                        stats["files_downloaded"] += 1
                    elif result["action"] == "updated":
                        stats["files_updated"] += 1
                    elif result["action"] == "skipped":
                        stats["files_skipped"] += 1
                    
                    # Count by category
                    category = result.get("category", "General")
                    stats["categories"][category] = stats["categories"].get(category, 0) + 1
                    
                except Exception as e:
                    logger.error(f"Error syncing file {drive_file['name']}: {e}")
                    stats["errors"] += 1
            
            stats["completed_at"] = datetime.now().isoformat()
            logger.info(f"Sync completed: {stats['files_downloaded']} downloaded, "
                       f"{stats['files_updated']} updated, {stats['files_skipped']} skipped")
            
            return stats
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            stats["status"] = "failed"
            stats["error"] = str(e)
            return stats
    
    def _list_drive_files_recursive(
        self,
        folder_id: str,
        path: str = ""
    ) -> List[Dict[str, Any]]:
        """
        List all files in folder recursively
        
        Args:
            folder_id: Drive folder ID
            path: Current path (for tracking structure)
        
        Returns:
            List of file metadata dicts
        """
        files = []
        
        try:
            # Query for files and folders
            query = f"'{folder_id}' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, md5Checksum, size)",
                pageSize=1000
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                # Build full path
                item_path = f"{path}/{item['name']}" if path else item['name']
                
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recurse into subfolder
                    subfolder_files = self._list_drive_files_recursive(
                        item['id'],
                        item_path
                    )
                    files.extend(subfolder_files)
                else:
                    # Add file with path
                    item['drive_path'] = item_path
                    files.append(item)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing Drive folder {folder_id}: {e}")
            return []
    
    def _sync_file(self, drive_file: Dict, force: bool = False) -> Dict[str, str]:
        """
        Sync single file from Drive
        
        Args:
            drive_file: Drive file metadata
            force: Force re-download
        
        Returns:
            Dict with action taken
        """
        file_id = drive_file['id']
        filename = drive_file['name']
        drive_path = drive_file['drive_path']
        drive_hash = drive_file.get('md5Checksum', '')
        
        # Determine category from path
        category = self._detect_category(drive_path)
        
        # Local cache path
        local_path = self.cache_path / drive_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists and hash matches
        if local_path.exists() and not force:
            local_hash = self._compute_file_hash(str(local_path))
            
            if local_hash == drive_hash:
                # File unchanged
                return {
                    "action": "skipped",
                    "file": filename,
                    "category": category
                }
        
        # Download file
        logger.info(f"Downloading: {drive_path}")
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            with io.FileIO(str(local_path), 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            # Register in database
            self._register_file_in_db(
                filepath=str(local_path),
                filename=filename,
                drive_path=drive_path,
                category=category,
                file_hash=drive_hash,
                size=drive_file.get('size', 0)
            )
            
            action = "updated" if local_path.exists() else "downloaded"
            
            return {
                "action": action,
                "file": filename,
                "category": category
            }
            
        except Exception as e:
            logger.error(f"Error downloading {filename}: {e}")
            return {
                "action": "error",
                "file": filename,
                "error": str(e)
            }
    
    def _detect_category(self, drive_path: str) -> str:
        """
        Detect category from Drive path
        
        Args:
            drive_path: Path in Drive (e.g., "PMI/PMBOK_Guide.pdf")
        
        Returns:
            Category name
        """
        path_lower = drive_path.lower()
        
        # Get configured categories
        categories = self.config.get("library.categories", [])
        
        for cat_config in categories:
            cat_name = cat_config.get('name', '')
            patterns = cat_config.get('patterns', [])
            
            for pattern in patterns:
                pattern_lower = pattern.lower().strip('/')
                if path_lower.startswith(pattern_lower):
                    return cat_name
        
        return "General"
    
    def _compute_file_hash(self, filepath: str) -> str:
        """Compute MD5 hash of file"""
        md5 = hashlib.md5()
        
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            logger.error(f"Error computing hash for {filepath}: {e}")
            return ""
    
    def _register_file_in_db(
        self,
        filepath: str,
        filename: str,
        drive_path: str,
        category: str,
        file_hash: str,
        size: int
    ):
        """Register file in unified database"""
        try:
            # Get file extension
            file_ext = Path(filename).suffix.lower().strip('.')
            
            # Check if already registered
            existing = self.db.get_file_by_path("LIBRARY", drive_path)
            
            if existing:
                # Update
                self.db.update_file(
                    existing['id'],
                    file_hash=file_hash,
                    file_size=size,
                    status="indexed",
                    metadata={
                        "category": category,
                        "drive_path": drive_path,
                        "synced_at": datetime.now().isoformat()
                    }
                )
                logger.debug(f"Updated file in DB: {filename}")
            else:
                # Insert
                self.db.add_file(
                    project_id="LIBRARY",
                    filename=filename,
                    file_path=drive_path,
                    file_type=file_ext,
                    file_hash=file_hash,
                    file_size=size,
                    status="pending",  # Will be indexed by RAG
                    metadata={
                        "category": category,
                        "drive_path": drive_path,
                        "synced_at": datetime.now().isoformat()
                    }
                )
                logger.debug(f"Registered file in DB: {filename}")
                
        except Exception as e:
            logger.error(f"Error registering file {filename} in DB: {e}")
    
    def watch_for_changes(self, callback=None):
        """
        Watch for changes in Drive folder (polling-based)
        
        Note: For production, use Drive API push notifications
        This is a simple polling implementation
        
        Args:
            callback: Function to call on changes detected
        """
        if not self.is_available():
            logger.warning("Drive watch not available")
            return
        
        logger.info("Starting Drive change watcher (polling mode)")
        
        # Store last known state
        last_state = {}
        
        import time
        check_interval = self.config.get("library.sync_interval_minutes", 60) * 60
        
        while True:
            try:
                # List current files
                current_files = self._list_drive_files_recursive(self.library_folder_id)
                current_state = {f['id']: f['modifiedTime'] for f in current_files}
                
                # Detect changes
                if last_state:
                    changes = []
                    
                    # New or modified files
                    for file_id, modified_time in current_state.items():
                        if file_id not in last_state or last_state[file_id] != modified_time:
                            changes.append(file_id)
                    
                    if changes:
                        logger.info(f"Detected {len(changes)} changes in Drive")
                        
                        # Trigger sync
                        sync_result = self.sync_library()
                        
                        if callback:
                            callback(sync_result)
                
                last_state = current_state
                
                # Wait before next check
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in change watcher: {e}")
                time.sleep(60)  # Wait 1 min on error


def create_drive_sync(db_manager, config) -> Optional[GoogleDriveSync]:
    """
    Factory function to create Drive sync instance
    
    Returns:
        GoogleDriveSync instance or None if not configured
    """
    try:
        sync = GoogleDriveSync(db_manager, config)
        
        if sync.is_available():
            logger.info("Google Drive sync available")
            return sync
        else:
            logger.info("Google Drive sync not configured")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create Drive sync: {e}")
        return None
