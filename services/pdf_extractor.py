"""PDF text extraction module for contract processing."""

import logging
from typing import Optional, Tuple
from pathlib import Path
import PyPDF2
import pdfplumber
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Base exception for PDF extraction errors."""
    pass


class CorruptedFileError(PDFExtractionError):
    """Raised when PDF file is corrupted or unreadable."""
    pass


class PasswordProtectedError(PDFExtractionError):
    """Raised when PDF is password protected."""
    pass


class PDFExtractor:
    """Extract text from PDF documents using multiple methods."""
    
    def __init__(self):
        """Initialize PDF extractor."""
        self.logger = logging.getLogger(__name__)
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF using best available method.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            CorruptedFileError: If PDF is corrupted
            PasswordProtectedError: If PDF is password protected
            PDFExtractionError: For other extraction errors
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise PDFExtractionError(f"File not found: {file_path}")
        
        # Try pdfplumber first (better for structured PDFs)
        try:
            text = self._extract_with_pdfplumber(file_path)
            if text and len(text.strip()) > 50:  # Minimum viable text
                self.logger.info(f"Successfully extracted text using pdfplumber: {len(text)} chars")
                return self._clean_text(text)
        except Exception as e:
            self.logger.warning(f"pdfplumber extraction failed: {e}")
        
        # Fallback to PyPDF2
        try:
            text = self._extract_with_pypdf2(file_path)
            if text and len(text.strip()) > 50:
                self.logger.info(f"Successfully extracted text using PyPDF2: {len(text)} chars")
                return self._clean_text(text)
        except Exception as e:
            self.logger.warning(f"PyPDF2 extraction failed: {e}")
        
        # If both fail, raise error
        raise PDFExtractionError(
            "Failed to extract text from PDF. File may be image-based or corrupted. "
            "Try using OCR extraction instead."
        )
    
    def _extract_with_pdfplumber(self, file_path: Path) -> str:
        """
        Extract text using pdfplumber library.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text_parts = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                            self.logger.debug(f"Extracted page {page_num}: {len(page_text)} chars")
                    except Exception as e:
                        self.logger.warning(f"Failed to extract page {page_num}: {e}")
                        continue
        except Exception as e:
            if "password" in str(e).lower():
                raise PasswordProtectedError("PDF is password protected")
            raise PDFExtractionError(f"pdfplumber error: {e}")
        
        return "\n\n".join(text_parts)
    
    def _extract_with_pypdf2(self, file_path: Path) -> str:
        """
        Extract text using PyPDF2 library.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        text_parts = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if encrypted
                if pdf_reader.is_encrypted:
                    raise PasswordProtectedError("PDF is password protected")
                
                num_pages = len(pdf_reader.pages)
                self.logger.debug(f"PDF has {num_pages} pages")
                
                for page_num in range(num_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                            self.logger.debug(f"Extracted page {page_num + 1}: {len(page_text)} chars")
                    except Exception as e:
                        self.logger.warning(f"Failed to extract page {page_num + 1}: {e}")
                        continue
                        
        except PasswordProtectedError:
            raise
        except Exception as e:
            if "EOF marker" in str(e) or "corrupted" in str(e).lower():
                raise CorruptedFileError(f"PDF file appears corrupted: {e}")
            raise PDFExtractionError(f"PyPDF2 error: {e}")
        
        return "\n\n".join(text_parts)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip whitespace
            line = line.strip()
            # Skip empty lines
            if line:
                # Normalize multiple spaces to single space
                line = ' '.join(line.split())
                cleaned_lines.append(line)
        
        # Join with single newline
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove common PDF artifacts
        cleaned_text = cleaned_text.replace('\x00', '')  # Null bytes
        cleaned_text = cleaned_text.replace('\ufffd', '')  # Replacement character
        
        return cleaned_text
    
    def is_image_based_pdf(self, file_path: str) -> bool:
        """
        Check if PDF is image-based (scanned) rather than text-based.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if PDF appears to be image-based
        """
        try:
            text = self.extract_text(file_path)
            # If we get very little text, it's likely image-based
            return len(text.strip()) < 100
        except PDFExtractionError:
            # If extraction fails, assume it's image-based
            return True
