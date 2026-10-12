"""Services package."""

# Core services are imported on-demand to avoid circular dependencies
# and missing optional dependencies

__all__ = [
    'PDFExtractor',
    'PDFExtractionError',
    'PasswordProtectedError',
    'CorruptedFileError',
    'OCRExtractor',
    'OCRError',
    'ClauseSegmenter',
    'DocumentProcessor',
    'DocumentProcessingError',
    'UnsupportedFormatError',
]
