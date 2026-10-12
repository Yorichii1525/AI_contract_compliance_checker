"""
Comprehensive error handling utilities for the compliance checker application.
Provides custom exceptions, error messages, and fallback mechanisms.
"""
import logging
import traceback
from typing import Optional, Dict, Any, Callable
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification."""
    DOCUMENT_PROCESSING = "document_processing"
    MODEL_INFERENCE = "model_inference"
    COMPLIANCE_CHECKING = "compliance_checking"
    DATA_VALIDATION = "data_validation"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"


# ============================================================================
# Custom Exception Classes
# ============================================================================

class ComplianceCheckerError(Exception):
    """Base exception for all compliance checker errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.details = details or {}
    
    def _generate_user_message(self) -> str:
        """Generate a user-friendly error message."""
        return "An error occurred. Please try again or contact support."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/reporting."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "user_message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details
        }


# Document Processing Errors
class DocumentProcessingError(ComplianceCheckerError):
    """Base exception for document processing errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.DOCUMENT_PROCESSING)
        super().__init__(message, **kwargs)


class UnsupportedFormatError(DocumentProcessingError):
    """Raised when file format is not supported."""
    
    def _generate_user_message(self) -> str:
        return (
            "The uploaded file format is not supported. "
            "Please upload a PDF, DOCX, TXT, PNG, or JPG file."
        )


class FileReadError(DocumentProcessingError):
    """Raised when file cannot be read."""
    
    def _generate_user_message(self) -> str:
        return (
            "Unable to read the uploaded file. "
            "The file may be corrupted or password-protected."
        )


class OCRError(DocumentProcessingError):
    """Raised when OCR processing fails."""
    
    def _generate_user_message(self) -> str:
        return (
            "Unable to extract text from the image. "
            "Please ensure the image is clear and contains readable text."
        )


class TextExtractionError(DocumentProcessingError):
    """Raised when text extraction fails."""
    
    def _generate_user_message(self) -> str:
        return (
            "Unable to extract text from the document. "
            "Please try a different file or contact support."
        )


# Model Inference Errors
class ModelError(ComplianceCheckerError):
    """Base exception for ML model errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.MODEL_INFERENCE)
        super().__init__(message, **kwargs)


class ModelLoadError(ModelError):
    """Raised when model fails to load."""
    
    def __init__(self, message: str, model_name: str = "unknown", **kwargs):
        kwargs.setdefault('severity', ErrorSeverity.CRITICAL)
        kwargs.setdefault('details', {}).update({'model_name': model_name})
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        return (
            "The AI model is temporarily unavailable. "
            "Please try again in a few moments."
        )


class InferenceError(ModelError):
    """Raised when model inference fails."""
    
    def _generate_user_message(self) -> str:
        return (
            "An error occurred during analysis. "
            "Please try again or try with a different document."
        )


class LowConfidenceError(ModelError):
    """Raised when model confidence is too low."""
    
    def __init__(self, message: str, confidence: float = 0.0, **kwargs):
        kwargs.setdefault('severity', ErrorSeverity.LOW)
        kwargs.setdefault('details', {}).update({'confidence': confidence})
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        return (
            "The analysis has low confidence. "
            "Manual review is recommended for accurate results."
        )


# Compliance Checking Errors
class ComplianceCheckError(ComplianceCheckerError):
    """Base exception for compliance checking errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.COMPLIANCE_CHECKING)
        super().__init__(message, **kwargs)


class RegulatoryDataMissingError(ComplianceCheckError):
    """Raised when regulatory data is missing."""
    
    def __init__(self, message: str, framework: str = "unknown", **kwargs):
        kwargs.setdefault('details', {}).update({'framework': framework})
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        framework = self.details.get('framework', 'the selected')
        return (
            f"Regulatory data for {framework} framework is not available. "
            "Please select a different framework or contact support."
        )


# Validation Errors
class ValidationError(ComplianceCheckerError):
    """Base exception for validation errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.DATA_VALIDATION)
        kwargs.setdefault('severity', ErrorSeverity.LOW)
        super().__init__(message, **kwargs)


class InvalidInputError(ValidationError):
    """Raised when user input is invalid."""
    
    def __init__(self, message: str, field: str = "unknown", **kwargs):
        kwargs.setdefault('details', {}).update({'field': field})
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        field = self.details.get('field', 'input')
        return f"Invalid {field}. Please check your input and try again."


class FileSizeError(ValidationError):
    """Raised when file size exceeds limit."""
    
    def __init__(self, message: str, size_mb: float = 0, max_mb: float = 10, **kwargs):
        kwargs.setdefault('details', {}).update({
            'size_mb': size_mb,
            'max_mb': max_mb
        })
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        max_mb = self.details.get('max_mb', 10)
        return f"File size exceeds the maximum limit of {max_mb}MB. Please upload a smaller file."


class EmptyDocumentError(ValidationError):
    """Raised when document has no content."""
    
    def _generate_user_message(self) -> str:
        return (
            "The document appears to be empty or contains no readable text. "
            "Please upload a document with content."
        )


# External Service Errors
class ExternalServiceError(ComplianceCheckerError):
    """Base exception for external service errors."""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.EXTERNAL_SERVICE)
        super().__init__(message, **kwargs)


class GoogleSheetsError(ExternalServiceError):
    """Raised when Google Sheets integration fails."""
    
    def _generate_user_message(self) -> str:
        return (
            "Unable to connect to Google Sheets. "
            "Please check the URL and ensure the sheet is shared correctly."
        )


# ============================================================================
# Error Handler Decorator
# ============================================================================

def handle_errors(
    fallback_value: Any = None,
    log_traceback: bool = True,
    reraise: bool = False
):
    """
    Decorator to handle errors gracefully with logging and fallback.
    
    Args:
        fallback_value: Value to return if error occurs
        log_traceback: Whether to log full traceback
        reraise: Whether to reraise the exception after handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ComplianceCheckerError as e:
                # Log custom exceptions
                logger.error(
                    f"Error in {func.__name__}: {e.message}",
                    extra=e.to_dict()
                )
                if log_traceback:
                    logger.debug(traceback.format_exc())
                
                if reraise:
                    raise
                return fallback_value
            
            except Exception as e:
                # Log unexpected exceptions
                logger.exception(f"Unexpected error in {func.__name__}: {e}")
                
                if reraise:
                    raise
                return fallback_value
        
        return wrapper
    return decorator


# ============================================================================
# Error Message Formatter
# ============================================================================

class ErrorMessageFormatter:
    """Format error messages for display to users."""
    
    @staticmethod
    def format_for_ui(error: Exception) -> Dict[str, str]:
        """
        Format error for UI display.
        
        Args:
            error: Exception to format
            
        Returns:
            Dictionary with title, message, and severity
        """
        if isinstance(error, ComplianceCheckerError):
            return {
                "title": error.__class__.__name__.replace("Error", " Error"),
                "message": error.user_message,
                "severity": error.severity.value,
                "category": error.category.value
            }
        else:
            return {
                "title": "Unexpected Error",
                "message": "An unexpected error occurred. Please try again or contact support.",
                "severity": ErrorSeverity.HIGH.value,
                "category": ErrorCategory.SYSTEM.value
            }
    
    @staticmethod
    def get_troubleshooting_tips(error: Exception) -> list:
        """
        Get troubleshooting tips for an error.
        
        Args:
            error: Exception to get tips for
            
        Returns:
            List of troubleshooting tips
        """
        tips_map = {
            UnsupportedFormatError: [
                "Ensure your file is in PDF, DOCX, TXT, PNG, or JPG format",
                "Try converting your file to PDF format",
                "Check that the file extension matches the actual file type"
            ],
            FileReadError: [
                "Verify the file is not corrupted",
                "If the file is password-protected, remove the password first",
                "Try re-saving the file and uploading again"
            ],
            OCRError: [
                "Ensure the image is clear and high-resolution",
                "Try scanning the document at a higher DPI (300+ recommended)",
                "Verify the text in the image is readable",
                "Consider converting the image to PDF first"
            ],
            ModelLoadError: [
                "Wait a few moments and try again",
                "Check your internet connection",
                "Contact support if the issue persists"
            ],
            GoogleSheetsError: [
                "Verify the Google Sheets URL is correct",
                "Ensure the sheet is shared with the service account",
                "Check that the sheet contains data in the specified range",
                "Verify your Google API credentials are configured"
            ],
            FileSizeError: [
                "Compress the file to reduce its size",
                "Split large documents into smaller sections",
                "Remove unnecessary images or attachments"
            ],
            EmptyDocumentError: [
                "Verify the document contains text",
                "If it's a scanned document, ensure OCR is enabled",
                "Try opening the file to confirm it has content"
            ]
        }
        
        error_type = type(error)
        return tips_map.get(error_type, [
            "Try again with a different file",
            "Check your input and try again",
            "Contact support if the issue persists"
        ])


# ============================================================================
# Fallback Mechanisms
# ============================================================================

class FallbackHandler:
    """Provide fallback mechanisms for various failures."""
    
    @staticmethod
    def create_fallback_clause_analysis(clause_id: str, clause_text: str):
        """Create a fallback clause analysis when processing fails."""
        from models.clause_analysis import ClauseAnalysis
        
        return ClauseAnalysis(
            clause_id=clause_id,
            clause_text=clause_text,
            clause_type="Other",
            confidence_score=0.0,
            embeddings=None,
            alternative_types=[("Other", 0.0)]
        )
    
    @staticmethod
    def create_fallback_compliance_report(document_id: str, frameworks: list):
        """Create a fallback compliance report when checking fails."""
        from models.regulatory_requirement import ComplianceReport, ComplianceSummary
        
        return ComplianceReport(
            document_id=document_id,
            frameworks_checked=frameworks,
            overall_score=0.0,
            clause_results=[],
            missing_requirements=[],
            high_risk_items=[],
            summary=ComplianceSummary(
                total_clauses=0,
                compliant_clauses=0,
                non_compliant_clauses=0,
                partial_clauses=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0
            )
        )
    
    @staticmethod
    def create_fallback_processed_document(filename: str, error_msg: str):
        """Create a fallback processed document when processing fails."""
        from models.processed_document import ProcessedDocument
        import uuid
        
        return ProcessedDocument(
            document_id=str(uuid.uuid4()),
            original_filename=filename,
            extracted_text=f"Error: {error_msg}",
            clauses=[],
            metadata={'error': error_msg},
            processing_time=0.0
        )


# ============================================================================
# Input Validators
# ============================================================================

class InputValidator:
    """Validate user inputs before processing."""
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: float = 10) -> None:
        """
        Validate file size.
        
        Args:
            file_size: File size in bytes
            max_size_mb: Maximum allowed size in MB
            
        Raises:
            FileSizeError: If file size exceeds limit
        """
        max_bytes = max_size_mb * 1024 * 1024
        if file_size > max_bytes:
            size_mb = file_size / (1024 * 1024)
            raise FileSizeError(
                f"File size {size_mb:.1f}MB exceeds maximum {max_size_mb}MB",
                size_mb=size_mb,
                max_mb=max_size_mb
            )
    
    @staticmethod
    def validate_text_input(text: str, min_length: int = 100) -> None:
        """
        Validate text input.
        
        Args:
            text: Input text
            min_length: Minimum required length
            
        Raises:
            InvalidInputError: If text is invalid
        """
        if not text or not text.strip():
            raise InvalidInputError(
                "Text input is empty",
                field="text"
            )
        
        if len(text.strip()) < min_length:
            raise InvalidInputError(
                f"Text too short (minimum {min_length} characters)",
                field="text",
                details={'length': len(text.strip()), 'min_length': min_length}
            )
    
    @staticmethod
    def validate_frameworks(frameworks: list) -> None:
        """
        Validate regulatory frameworks selection.
        
        Args:
            frameworks: List of framework names
            
        Raises:
            InvalidInputError: If frameworks are invalid
        """
        if not frameworks:
            raise InvalidInputError(
                "No frameworks selected",
                field="frameworks"
            )
        
        valid_frameworks = {'GDPR', 'HIPAA', 'CCPA', 'SOX'}
        invalid = [f for f in frameworks if f.upper() not in valid_frameworks]
        
        if invalid:
            raise InvalidInputError(
                f"Invalid frameworks: {', '.join(invalid)}",
                field="frameworks",
                details={'invalid_frameworks': invalid}
            )
    
    @staticmethod
    def validate_confidence_threshold(threshold: float) -> None:
        """
        Validate confidence threshold.
        
        Args:
            threshold: Confidence threshold value
            
        Raises:
            InvalidInputError: If threshold is invalid
        """
        if not 0.0 <= threshold <= 1.0:
            raise InvalidInputError(
                f"Confidence threshold must be between 0.0 and 1.0, got {threshold}",
                field="confidence_threshold"
            )
    
    @staticmethod
    def validate_google_sheets_url(url: str) -> None:
        """
        Validate Google Sheets URL format.
        
        Args:
            url: Google Sheets URL
            
        Raises:
            InvalidInputError: If URL is invalid
        """
        if not url or not url.strip():
            raise InvalidInputError(
                "Google Sheets URL is empty",
                field="google_sheets_url"
            )
        
        if "docs.google.com/spreadsheets" not in url:
            raise InvalidInputError(
                "Invalid Google Sheets URL format",
                field="google_sheets_url"
            )


# ============================================================================
# Error Recovery Strategies
# ============================================================================

class ErrorRecoveryStrategy:
    """Strategies for recovering from errors."""
    
    @staticmethod
    def retry_with_backoff(
        func: Callable,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds
            backoff_factor: Backoff multiplier
            
        Returns:
            Function result or raises last exception
        """
        import time
        
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
        
        logger.error(f"All {max_retries} attempts failed")
        raise last_exception
    
    @staticmethod
    def fallback_chain(funcs: list, default_value: Any = None):
        """
        Try functions in sequence until one succeeds.
        
        Args:
            funcs: List of functions to try
            default_value: Value to return if all fail
            
        Returns:
            Result from first successful function or default_value
        """
        for i, func in enumerate(funcs):
            try:
                return func()
            except Exception as e:
                logger.warning(f"Fallback {i + 1}/{len(funcs)} failed: {e}")
                continue
        
        logger.error("All fallback options failed")
        return default_value
