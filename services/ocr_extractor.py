"""OCR text extraction module for image-based documents."""

import logging
from typing import Optional, Tuple, List
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import pytesseract
import pdfplumber

logger = logging.getLogger(__name__)


class OCRError(Exception):
    """Base exception for OCR errors."""
    pass


class OCRExtractor:
    """Extract text from image-based documents using Tesseract OCR."""
    
    def __init__(self, min_confidence: float = 0.5, verify_installation: bool = True):
        """
        Initialize OCR extractor.
        
        Args:
            min_confidence: Minimum confidence threshold for OCR results (0-1)
            verify_installation: Whether to verify Tesseract installation on init
        """
        self.logger = logging.getLogger(__name__)
        self.min_confidence = min_confidence
        self._tesseract_available = None
        
        # Verify Tesseract is available if requested
        if verify_installation:
            self._check_tesseract()
    
    def _check_tesseract(self):
        """Check if Tesseract is available."""
        try:
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            self.logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            self._tesseract_available = False
            self.logger.error(f"Tesseract not found: {e}")
            raise OCRError(
                "Tesseract OCR not installed. Please install Tesseract: "
                "https://github.com/tesseract-ocr/tesseract"
            )
    
    def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from image file (PNG, JPG, etc.).
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (extracted_text, confidence_score)
            
        Raises:
            OCRError: If OCR extraction fails
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise OCRError(f"Image file not found: {image_path}")
        
        try:
            # Load and preprocess image
            image = cv2.imread(str(image_path))
            if image is None:
                raise OCRError(f"Failed to load image: {image_path}")
            
            preprocessed = self._preprocess_image(image)
            
            # Perform OCR with confidence data
            text, confidence = self._ocr_with_confidence(preprocessed)
            
            self.logger.info(
                f"OCR extracted {len(text)} chars with {confidence:.2%} confidence"
            )
            
            return text, confidence
            
        except OCRError:
            raise
        except Exception as e:
            raise OCRError(f"OCR extraction failed: {e}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, float]:
        """
        Extract text from image-based PDF using OCR.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, average_confidence_score)
            
        Raises:
            OCRError: If OCR extraction fails
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise OCRError(f"PDF file not found: {pdf_path}")
        
        try:
            text_parts = []
            confidences = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Convert PDF page to image
                        pil_image = page.to_image(resolution=300).original
                        
                        # Convert PIL to OpenCV format
                        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                        
                        # Preprocess and OCR
                        preprocessed = self._preprocess_image(image)
                        page_text, confidence = self._ocr_with_confidence(preprocessed)
                        
                        if page_text.strip():
                            text_parts.append(page_text)
                            confidences.append(confidence)
                            self.logger.debug(
                                f"Page {page_num}: {len(page_text)} chars, "
                                f"{confidence:.2%} confidence"
                            )
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to OCR page {page_num}: {e}")
                        continue
            
            if not text_parts:
                raise OCRError("No text extracted from PDF")
            
            combined_text = "\n\n".join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            self.logger.info(
                f"OCR extracted {len(combined_text)} chars from {len(text_parts)} pages "
                f"with {avg_confidence:.2%} average confidence"
            )
            
            return combined_text, avg_confidence
            
        except OCRError:
            raise
        except Exception as e:
            raise OCRError(f"PDF OCR extraction failed: {e}")
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy.
        
        Applies:
        - Grayscale conversion
        - Noise reduction
        - Deskewing
        - Contrast enhancement
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Deskew
        deskewed = self._deskew_image(denoised)
        
        # Contrast enhancement using adaptive thresholding
        enhanced = cv2.adaptiveThreshold(
            deskewed,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        return enhanced
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew (straighten) a rotated image.
        
        Args:
            image: Input grayscale image
            
        Returns:
            Deskewed image
        """
        # Calculate skew angle
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image
        
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Only deskew if angle is significant
        if abs(angle) < 0.5:
            return image
        
        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        self.logger.debug(f"Deskewed image by {angle:.2f} degrees")
        return rotated
    
    def _ocr_with_confidence(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Perform OCR and calculate confidence score.
        
        Args:
            image: Preprocessed image
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        # Get detailed OCR data
        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            config='--psm 1'  # Automatic page segmentation with OSD
        )
        
        # Extract text and confidence
        text_parts = []
        confidences = []
        
        for i, conf in enumerate(ocr_data['conf']):
            text = ocr_data['text'][i].strip()
            
            # Skip empty text or low confidence
            if text and conf != -1:  # -1 means no confidence data
                text_parts.append(text)
                confidences.append(float(conf) / 100.0)  # Convert to 0-1 scale
        
        # Combine text with proper spacing
        full_text = self._reconstruct_text(ocr_data)
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Warn if confidence is low
        if avg_confidence < self.min_confidence:
            self.logger.warning(
                f"OCR confidence {avg_confidence:.2%} below threshold "
                f"{self.min_confidence:.2%}"
            )
        
        return full_text, avg_confidence
    
    def _reconstruct_text(self, ocr_data: dict) -> str:
        """
        Reconstruct text from OCR data with proper formatting.
        
        Args:
            ocr_data: Tesseract OCR output data
            
        Returns:
            Reconstructed text with proper line breaks
        """
        lines = []
        current_line = []
        current_line_num = -1
        
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            line_num = ocr_data['line_num'][i]
            
            if not text:
                continue
            
            # New line detected
            if line_num != current_line_num:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [text]
                current_line_num = line_num
            else:
                current_line.append(text)
        
        # Add last line
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
