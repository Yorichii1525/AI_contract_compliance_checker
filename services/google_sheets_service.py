"""Google Sheets integration service for contract text extraction."""

import logging
import re
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class GoogleSheetsError(Exception):
    """Base exception for Google Sheets errors."""
    pass


class AuthenticationError(GoogleSheetsError):
    """Raised when authentication fails."""
    pass


class SheetNotFoundError(GoogleSheetsError):
    """Raised when sheet is not found or not accessible."""
    pass


class GoogleSheetsService:
    """Service for extracting contract text from Google Sheets."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets service.
        
        Args:
            credentials_path: Path to Google API credentials JSON file
        """
        self.logger = logging.getLogger(__name__)
        self.credentials_path = credentials_path or self._get_default_credentials_path()
        self._service = None
    
    def _get_default_credentials_path(self) -> str:
        """Get default credentials path."""
        return str(Path(__file__).parent.parent / 'config' / 'google_credentials.json')
    
    def _initialize_service(self):
        """Initialize Google Sheets API service."""
        if self._service is not None:
            return
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # Check if credentials file exists
            if not Path(self.credentials_path).exists():
                raise AuthenticationError(
                    f"Google API credentials not found at {self.credentials_path}. "
                    "Please download credentials from Google Cloud Console and place them in the config folder."
                )
            
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            
            # Build service
            self._service = build('sheets', 'v4', credentials=credentials)
            self.logger.info("Google Sheets service initialized successfully")
            
        except ImportError:
            raise GoogleSheetsError(
                "Google API libraries not installed. "
                "Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        except Exception as e:
            raise AuthenticationError(f"Failed to authenticate with Google Sheets API: {e}")
    
    def parse_sheet_url(self, url: str) -> Tuple[str, Optional[str]]:
        """
        Parse Google Sheets URL to extract spreadsheet ID and sheet name.
        
        Args:
            url: Google Sheets URL
            
        Returns:
            Tuple of (spreadsheet_id, sheet_name)
            
        Raises:
            GoogleSheetsError: If URL is invalid
        """
        # Pattern for Google Sheets URLs
        # https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sheet_id}
        # https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit
        
        pattern = r'^https?://docs\.google\.com/spreadsheets/(?:u/\d+/)?d/([a-zA-Z0-9_-]+)(?:[/?#].*)?$'
        match = re.match(pattern, url.strip())
        
        if not match:
            raise GoogleSheetsError(
                "Invalid Google Sheets URL. Expected format: "
                "https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            )
        
        spreadsheet_id = match.group(1)
        
        # A gid identifies a tab, not its title. Resolve it when fetching metadata.
        gid_match = re.search(r'[?&#]gid=(\d+)', url)
        sheet_name = f"gid:{gid_match.group(1)}" if gid_match else None
        
        return spreadsheet_id, sheet_name
    
    def extract_text_from_sheet(
        self,
        url: str,
        sheet_name: Optional[str] = None,
        cell_range: Optional[str] = None
    ) -> str:
        """
        Extract contract text from Google Sheets.
        
        Args:
            url: Google Sheets URL
            sheet_name: Optional sheet name (defaults to first sheet)
            cell_range: Optional cell range (e.g., 'A1:B10'). If not provided, reads all data.
            
        Returns:
            Extracted text from the sheet
            
        Raises:
            GoogleSheetsError: If extraction fails
        """
        try:
            # Initialize service if needed
            self._initialize_service()
            
            # Parse URL
            spreadsheet_id, parsed_sheet_name = self.parse_sheet_url(url)
            
            # Use provided sheet name or parsed one
            if not sheet_name:
                sheet_name = parsed_sheet_name
            
            # Build range string
            if sheet_name and sheet_name.startswith("gid:") or not sheet_name:
                sheet_metadata = self._service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id
                ).execute()
                
                sheets = sheet_metadata.get('sheets', [])
                if not sheets:
                    raise SheetNotFoundError("No sheets found in the spreadsheet")
                
                if not sheets:
                    raise SheetNotFoundError("No sheets found in the spreadsheet")
                if sheet_name and sheet_name.startswith("gid:"):
                    gid = int(sheet_name.split(":", 1)[1])
                    selected = next((s['properties'] for s in sheets if s['properties'].get('sheetId') == gid), None)
                    if selected is None:
                        raise SheetNotFoundError(f"No tab with gid {gid} was found")
                    sheet_name = selected['title']
                else:
                    sheet_name = sheets[0]['properties']['title']

            # Quote tab titles so spaces and apostrophes are valid in A1 notation.
            quoted_name = "'" + sheet_name.replace("'", "''") + "'" if sheet_name else None
            range_str = f"{quoted_name}!{cell_range}" if cell_range and quoted_name else (cell_range or quoted_name)
            
            self.logger.info(f"Reading from spreadsheet {spreadsheet_id}, range: {range_str}")
            
            # Read data from sheet
            result = self._service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_str
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                raise GoogleSheetsError("No data found in the specified range")
            
            # Convert rows to text
            text_lines = []
            for row in values:
                # Join cells in row with space
                row_text = ' '.join(str(cell) for cell in row if cell)
                if row_text.strip():
                    text_lines.append(row_text)
            
            extracted_text = '\n'.join(text_lines)
            
            self.logger.info(f"Successfully extracted {len(extracted_text)} characters from Google Sheets")
            
            return extracted_text
            
        except (AuthenticationError, SheetNotFoundError, GoogleSheetsError):
            raise
        except Exception as e:
            self.logger.exception(f"Error extracting text from Google Sheets: {e}")
            raise GoogleSheetsError(f"Failed to extract text from Google Sheets: {e}")
    
    def validate_url(self, url: str) -> bool:
        """
        Validate Google Sheets URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid
        """
        try:
            self.parse_sheet_url(url)
            return True
        except GoogleSheetsError:
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to Google Sheets API.
        
        Returns:
            True if connection is successful
        """
        try:
            self._initialize_service()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
