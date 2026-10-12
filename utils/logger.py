"""
Logging utility with sanitization for sensitive data.
"""
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import sys


class SensitiveDataFilter(logging.Filter):
    """Filter to sanitize sensitive data from log messages."""
    
    # Patterns for sensitive data
    PATTERNS = {
        'email': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
        'phone': (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
        'ssn': (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
        'credit_card': (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]'),
        'api_key': (r'(api[_-]?key|apikey|access[_-]?token)["\s:=]+[A-Za-z0-9_\-]{20,}', '[API_KEY]'),
        'password': (r'(password|passwd|pwd)["\s:=]+\S+', 'password=[REDACTED]'),
        'bearer_token': (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer [TOKEN]'),
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitize sensitive data from log record."""
        record.msg = self._sanitize(str(record.msg))
        
        if record.args:
            record.args = tuple(
                self._sanitize(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True
    
    def _sanitize(self, text: str) -> str:
        """Replace sensitive data patterns with placeholders."""
        for pattern, replacement in self.PATTERNS.values():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text


class ComplianceLogger:
    """Custom logger for compliance checker application."""
    
    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        log_dir: Optional[Path] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        sanitize: bool = True
    ):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files
            enable_console: Enable console output
            enable_file: Enable file output
            sanitize: Enable sensitive data sanitization
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add sensitive data filter if enabled
        if sanitize:
            sensitive_filter = SensitiveDataFilter()
            self.logger.addFilter(sensitive_filter)
        
        # Console handler
        if enable_console:
            # Use utf-8 encoding to handle Unicode characters on Windows (avoids CP1252 errors)
            utf8_stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1, closefd=False)
            console_handler = logging.StreamHandler(utf8_stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if enable_file and log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create log file with timestamp
            log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message."""
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message."""
        self.logger.critical(message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)
    
    def log_performance(self, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Log performance metrics."""
        msg = f"Performance: {operation} completed in {duration:.2f}s"
        if metadata:
            msg += f" | Metadata: {metadata}"
        self.info(msg)
    
    def log_analysis_start(self, document_id: str, filename: str):
        """Log start of contract analysis."""
        self.info(f"Starting analysis for document: {document_id} (filename: {filename})")
    
    def log_analysis_complete(self, document_id: str, duration: float, score: float):
        """Log completion of contract analysis."""
        self.info(
            f"Analysis complete for document: {document_id} | "
            f"Duration: {duration:.2f}s | Score: {score:.1f}%"
        )
    
    def log_compliance_check(self, framework: str, status: str, risk_level: str):
        """Log compliance check result."""
        self.info(
            f"Compliance check: Framework={framework} | "
            f"Status={status} | Risk={risk_level}"
        )
    
    def log_model_load(self, model_name: str, duration: float):
        """Log model loading."""
        self.info(f"Model loaded: {model_name} in {duration:.2f}s")
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        """Log error with additional context."""
        self.error(
            f"Error occurred: {type(error).__name__}: {str(error)} | Context: {context}",
            exc_info=True
        )


def get_logger(
    name: str,
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    sanitize: bool = True
) -> ComplianceLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
        log_level: Logging level
        log_dir: Directory for log files
        sanitize: Enable sensitive data sanitization
    
    Returns:
        ComplianceLogger instance
    """
    return ComplianceLogger(
        name=name,
        log_level=log_level,
        log_dir=log_dir,
        sanitize=sanitize
    )
