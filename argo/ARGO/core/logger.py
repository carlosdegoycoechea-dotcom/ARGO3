"""
ARGO - Unified Logging System
Corporate-grade logging without emojis or decorations
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime


class CorporateFormatter(logging.Formatter):
    """
    Corporate-style formatter without emojis
    Clean, professional output
    """
    
    def format(self, record):
        # Standard format without decorations
        return super().format(record)


class ARGOLogger:
    """Unified logging system for ARGO"""
    
    _loggers = {}
    _initialized = False
    _log_dir = None
    
    @classmethod
    def initialize(cls, log_dir: Path, level: str = "INFO"):
        """
        Initialize logging system
        
        Args:
            log_dir: Directory for log files
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if cls._initialized:
            return
        
        cls._log_dir = Path(log_dir)
        cls._log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str, level: Optional[str] = None) -> logging.Logger:
        """
        Get or create a logger
        
        Args:
            name: Logger name (typically module name)
            level: Optional specific level for this logger
        
        Returns:
            Configured logger
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        # Create logger
        logger = logging.getLogger(name)
        
        # Set level
        if level:
            logger.setLevel(getattr(logging, level.upper()))
        
        # Remove any existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = CorporateFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (if initialized)
        if cls._initialized and cls._log_dir:
            log_file = cls._log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = CorporateFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        cls._loggers[name] = logger
        return logger


def get_logger(name: str = "argo", level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name
        level: Optional logging level
    
    Returns:
        Configured logger
    """
    return ARGOLogger.get_logger(name, level)


def initialize_logging(log_dir: Path, level: str = "INFO"):
    """
    Initialize the logging system
    
    Args:
        log_dir: Directory for log files
        level: Global logging level
    """
    ARGOLogger.initialize(log_dir, level)


class LogContext:
    """
    Context manager for temporary log level changes
    
    Example:
        with LogContext("rag_engine", "DEBUG"):
            # Detailed logging here
            rag_engine.process()
    """
    
    def __init__(self, logger_name: str, level: str):
        self.logger = get_logger(logger_name)
        self.original_level = self.logger.level
        self.new_level = getattr(logging, level.upper())
    
    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)
        return False


# Corporate message templates (no emojis)
class LogMessages:
    """Standard log message templates"""
    
    @staticmethod
    def system_init(component: str) -> str:
        return f"Initializing {component}"
    
    @staticmethod
    def system_ready(component: str) -> str:
        return f"{component} initialized successfully"
    
    @staticmethod
    def operation_start(operation: str) -> str:
        return f"Starting {operation}"
    
    @staticmethod
    def operation_complete(operation: str, duration_ms: float) -> str:
        return f"{operation} completed in {duration_ms:.2f}ms"
    
    @staticmethod
    def operation_failed(operation: str, error: str) -> str:
        return f"{operation} failed: {error}"
    
    @staticmethod
    def config_loaded(config_file: str) -> str:
        return f"Configuration loaded from {config_file}"
    
    @staticmethod
    def api_call(provider: str, model: str, tokens: int) -> str:
        return f"API call to {provider}/{model} - {tokens} tokens"
    
    @staticmethod
    def file_processed(filename: str, size_kb: float) -> str:
        return f"Processed file {filename} ({size_kb:.2f} KB)"
    
    @staticmethod
    def database_operation(operation: str, table: str, rows: int) -> str:
        return f"Database {operation} on {table}: {rows} rows affected"
    
    @staticmethod
    def warning_threshold(metric: str, current: float, threshold: float) -> str:
        return f"Warning: {metric} at {current:.1f}% (threshold: {threshold:.1f}%)"
    
    @staticmethod
    def error_with_context(component: str, error: str, context: str) -> str:
        return f"Error in {component}: {error} | Context: {context}"
