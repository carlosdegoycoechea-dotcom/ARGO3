"""
ARGO v8.0 - Files Manager
Gestión de archivos: upload, download, Drive sync
"""
from pathlib import Path
from typing import Dict, List
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

from core.logger import get_logger

logger = get_logger()


class FilesManager:
    """Gestor de archivos del sistema"""
    
    def __init__(self, credentials_file: Path = None):
        self.credentials = None
        self.drive_service = None
        
        if credentials_file and credentials_file.exists():
            self._init_drive_service(credentials_file)
    
    def _init_drive_service(self, credentials_file: Path):
        """Inicializa servicio de Google Drive"""
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                str(credentials_file),
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            logger.info("✓ Servicio Google Drive inicializado")
        except Exception as e:
            logger.error(f"Error inicializando Drive: {e}")
    
    def sync_drive_project(
        self,
        folder_id: str,
        destination_path: Path
    ) -> Dict:
        """
        Sincroniza carpeta Drive a path local
        
        Args:
            folder_id: ID de carpeta Google Drive
            destination_path: Path local de destino
        
        Returns:
            {
                'synced': int,
                'skipped': int,
                'errors': int,
                'total_size': int
            }
        """
        if not self.drive_service:
            return {
                'synced': 0,
                'skipped': 0,
                'errors': 0,
                'total_size': 0,
                'message': 'Drive no configurado'
            }
        
        destination_path.mkdir(parents=True, exist_ok=True)
        
        files = self._list_files_recursive(folder_id)
        
        stats = {'synced': 0, 'skipped': 0, 'errors': 0, 'total_size': 0}
        
        for file in files:
            try:
                local_path = destination_path / file['name']
                
                # Skip si existe y mismo tamaño
                if local_path.exists():
                    if local_path.stat().st_size == file['size']:
                        stats['skipped'] += 1
                        continue
                
                # Descargar
                self._download_file(file['id'], local_path)
                stats['synced'] += 1
                stats['total_size'] += file['size']
                
            except Exception as e:
                logger.error(f"Error descargando {file['name']}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def _list_files_recursive(self, folder_id: str) -> List[Dict]:
        """Lista archivos recursivamente"""
        query = f"'{folder_id}' in parents and trashed=false"
        
        results = self.drive_service.files().list(
            q=query,
            fields="files(id, name, mimeType, size, modifiedTime)",
            pageSize=1000
        ).execute()
        
        files = []
        
        for item in results.get('files', []):
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursivo para subcarpetas
                files.extend(self._list_files_recursive(item['id']))
            else:
                files.append({
                    'id': item['id'],
                    'name': item['name'],
                    'size': int(item.get('size', 0)),
                    'modified': item['modifiedTime']
                })
        
        return files
    
    def _download_file(self, file_id: str, destination: Path):
        """Descarga archivo de Drive"""
        request = self.drive_service.files().get_media(fileId=file_id)
        
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        with io.FileIO(destination, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
    
    def upload_local_file(
        self,
        file_path: Path,
        project_cache_path: Path
    ) -> Dict:
        """
        Copia archivo local al cache del proyecto
        
        Args:
            file_path: Path del archivo a subir
            project_cache_path: Path del cache del proyecto
        
        Returns:
            {'success': bool, 'path': Path}
        """
        try:
            destination = project_cache_path / file_path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(file_path, destination)
            
            return {'success': True, 'path': destination}
        except Exception as e:
            logger.error(f"Error subiendo archivo: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_project_files(self, project_cache_path: Path) -> List[Dict]:
        """Lista archivos en el cache del proyecto"""
        if not project_cache_path.exists():
            return []
        
        files = []
        for file_path in project_cache_path.iterdir():
            if file_path.is_file():
                files.append({
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'path': str(file_path)
                })
        
        return files
