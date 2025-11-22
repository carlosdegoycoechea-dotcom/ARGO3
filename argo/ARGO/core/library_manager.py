"""
ARGO v9.0 - Library Manager
Gestión de la Biblioteca Global de conocimiento (PMI, AACE, Standards, ED/STO Best Practices)
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from core.logger import get_logger

logger = get_logger("LibraryManager")


class LibraryManager:
    """
    Gestor de la Biblioteca Global
    
    La biblioteca es un proyecto especial que contiene:
    - Estándares PMI, AACE
    - Best practices ED/STO
    - Referencias de industria
    - Documentación técnica general
    
    Es accesible desde cualquier proyecto para enriquecer respuestas
    """
    
    LIBRARY_PROJECT_ID = "LIBRARY"
    LIBRARY_NAME = "Biblioteca Global"
    
    # Categorías de la biblioteca
    CATEGORIES = {
        "pmi": {"name": "PMI Standards", "weight": 1.2},
        "aace": {"name": "AACE Guidelines", "weight": 1.2},
        "standards": {"name": "Industry Standards", "weight": 1.1},
        "edsto": {"name": "ED/STO Best Practices", "weight": 1.3},
        "references": {"name": "Technical References", "weight": 1.0},
        "templates": {"name": "Templates & Tools", "weight": 0.9}
    }
    
    def __init__(self, db_manager, base_path: Path):
        """
        Args:
            db_manager: UnifiedDatabase instance
            base_path: Ruta base donde está la carpeta library/
        """
        self.db = db_manager
        self.base_path = Path(base_path)
        self.library_path = self.base_path / "library"
        
        # Asegurar que existe el proyecto biblioteca
        self._ensure_library_project()
        
        logger.info(f"LibraryManager inicializado - Path: {str(self.library_path)}")
    
    def _ensure_library_project(self):
        """Asegura que el proyecto LIBRARY existe"""
        existing = self.db.get_project(project_id=self.LIBRARY_PROJECT_ID)
        
        if not existing:
            # Crear proyecto biblioteca
            self.db.create_project(
                project_id=self.LIBRARY_PROJECT_ID,
                name=self.LIBRARY_NAME,
                base_path="library",
                description="Biblioteca global de conocimiento PMI, AACE, Standards y Best Practices",
                project_type="library",
                metadata={
                    "categories": list(self.CATEGORIES.keys()),
                    "global": True,
                    "accessible_from_all": True
                }
            )
            logger.info("Proyecto LIBRARY creado")
            
            # Crear estructura de carpetas
            self._create_library_structure()
        else:
            logger.debug("Proyecto LIBRARY ya existe")
    
    def _create_library_structure(self):
        """Crea la estructura de carpetas de la biblioteca"""
        for category_id, category_info in self.CATEGORIES.items():
            category_path = self.library_path / category_id
            category_path.mkdir(parents=True, exist_ok=True)
            
            # Crear README en cada categoría
            readme = category_path / "README.md"
            if not readme.exists():
                readme.write_text(
                    f"# {category_info['name']}\n\n"
                    f"Coloca aquí documentos de: {category_info['name']}\n\n"
                    f"Estos documentos estarán disponibles desde todos los proyectos.\n"
                )
        
        logger.info(f"Estructura de biblioteca creada en {self.library_path}")
    
    def get_library_info(self) -> Dict[str, Any]:
        """Obtiene información de la biblioteca"""
        project = self.db.get_project(project_id=self.LIBRARY_PROJECT_ID)
        
        if not project:
            return {}
        
        # Estadísticas
        files = self.db.get_project_files(self.LIBRARY_PROJECT_ID)
        stats = self.db.get_project_stats(self.LIBRARY_PROJECT_ID)
        
        # Contar por categoría
        by_category = {}
        for category_id in self.CATEGORIES.keys():
            category_files = [f for f in files if category_id in f.get('file_path', '')]
            by_category[category_id] = len(category_files)
        
        return {
            "project": project,
            "stats": stats,
            "by_category": by_category,
            "total_files": len(files),
            "categories": self.CATEGORIES
        }
    
    def should_use_library(self, query: str, project_type: str = "standard") -> bool:
        """
        Determina si se debe consultar la biblioteca para esta query
        
        Args:
            query: Query del usuario
            project_type: Tipo de proyecto actual
            
        Returns:
            True si se debe consultar la biblioteca
        """
        # Keywords que indican búsqueda de best practices/standards
        library_keywords = [
            "standard", "best practice", "guideline", "methodology",
            "pmbok", "pmi", "aace", "iso", "framework",
            "industry", "reference", "benchmark", "template",
            "procedure", "protocol", "specification"
        ]
        
        query_lower = query.lower()
        
        # Proyectos ED/STO siempre consultan biblioteca para best practices
        if project_type == "ed_sto":
            edsto_keywords = ["shutdown", "turnaround", "outage", "maintenance", "parada"]
            if any(kw in query_lower for kw in edsto_keywords):
                return True
        
        # Si menciona keywords de biblioteca
        if any(kw in query_lower for kw in library_keywords):
            return True
        
        # Queries sobre "cómo hacer" algo
        how_to_patterns = ["cómo", "como", "how to", "what is the best way", "cuál es la mejor"]
        if any(pattern in query_lower for pattern in how_to_patterns):
            return True
        
        return False
    
    def get_library_boost_factor(self, doc_metadata: Dict) -> float:
        """
        Calcula factor de boost para documentos de biblioteca
        
        Args:
            doc_metadata: Metadata del documento
            
        Returns:
            Factor multiplicador para el score (>1.0 = boost, <1.0 = penalty)
        """
        # Identificar categoría del documento
        file_path = doc_metadata.get('file_path', '')
        doc_type = doc_metadata.get('doc_type', '')
        
        # Boost por categoría
        for category_id, category_info in self.CATEGORIES.items():
            if category_id in file_path.lower() or category_id in doc_type.lower():
                return category_info['weight']
        
        # Default: boost moderado para cualquier cosa de biblioteca
        return 1.1
    
    def format_library_source(self, doc: Dict) -> str:
        """
        Formatea fuente de biblioteca para mostrar al usuario
        
        Args:
            doc: Documento de biblioteca
            
        Returns:
            String formateado para mostrar
        """
        filename = doc.get('filename', 'Unknown')
        file_path = doc.get('file_path', '')
        
        # Identificar categoría
        category_name = "Library"
        for category_id, category_info in self.CATEGORIES.items():
            if category_id in file_path.lower():
                category_name = category_info['name']
                break
        
        return f"📚 {category_name}: {filename}"
    
    def get_library_context_prefix(self, project_type: str = "standard") -> str:
        """
        Obtiene el prefijo de contexto para chunks de biblioteca
        
        Args:
            project_type: Tipo de proyecto actual
            
        Returns:
            String con prefijo para el prompt
        """
        if project_type == "ed_sto":
            return (
                "CONTEXTO DE BIBLIOTECA (Estándares y Best Practices ED/STO):\n"
                "Los siguientes fragmentos provienen de la biblioteca de conocimiento "
                "con estándares de industria, best practices de ED/STO y referencias técnicas.\n\n"
            )
        else:
            return (
                "CONTEXTO DE BIBLIOTECA (Estándares y Referencias):\n"
                "Los siguientes fragmentos provienen de la biblioteca de conocimiento "
                "con estándares PMI/AACE y referencias técnicas de industria.\n\n"
            )
    
    def get_recommended_categories(self, query: str) -> List[str]:
        """
        Recomienda qué categorías consultar según la query
        
        Args:
            query: Query del usuario
            
        Returns:
            Lista de category_ids relevantes
        """
        query_lower = query.lower()
        recommendations = []
        
        # Mapeo de keywords a categorías
        category_keywords = {
            "pmi": ["pmi", "pmbok", "project management", "gestión de proyectos"],
            "aace": ["aace", "cost", "schedule", "risk", "costo", "cronograma"],
            "standards": ["standard", "iso", "specification", "norm", "norma"],
            "edsto": ["shutdown", "turnaround", "outage", "maintenance", "parada", "ed/sto"],
            "references": ["reference", "guide", "manual", "handbook", "referencia"],
            "templates": ["template", "format", "form", "plantilla", "formato"]
        }
        
        for category_id, keywords in category_keywords.items():
            if any(kw in query_lower for kw in keywords):
                recommendations.append(category_id)
        
        # Si no hay recomendaciones específicas, sugerir las más generales
        if not recommendations:
            recommendations = ["standards", "references", "pmi"]
        
        return recommendations
    
    def is_library_document(self, doc_metadata: Dict) -> bool:
        """
        Verifica si un documento pertenece a la biblioteca
        
        Args:
            doc_metadata: Metadata del documento
            
        Returns:
            True si es de biblioteca
        """
        project_id = doc_metadata.get('project_id', '')
        return project_id == self.LIBRARY_PROJECT_ID


# Singleton instance
_library_manager_instance: Optional[LibraryManager] = None


def get_library_manager(db_manager=None, base_path: Path = None) -> LibraryManager:
    """
    Obtiene la instancia singleton del LibraryManager
    
    Args:
        db_manager: UnifiedDatabase (solo en primera llamada)
        base_path: Ruta base (solo en primera llamada)
    """
    global _library_manager_instance
    
    if _library_manager_instance is None:
        if db_manager is None or base_path is None:
            raise ValueError("Primera llamada requiere db_manager y base_path")
        
        _library_manager_instance = LibraryManager(db_manager, base_path)
    
    return _library_manager_instance
