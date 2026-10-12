"""Google Sheets Writer Service - Write compliance reports to Google Sheets."""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class GoogleSheetsWriterError(Exception):
    """Base exception for Google Sheets Writer errors."""
    pass


class GoogleSheetsWriter:
    """Service for writing compliance reports to Google Sheets."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets Writer service.
        
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
        """Initialize Google Sheets API service with write permissions."""
        if self._service is not None:
            return
        
        try:
            # Check if credentials file exists
            if not Path(self.credentials_path).exists():
                raise GoogleSheetsWriterError(
                    f"Google API credentials not found at {self.credentials_path}"
                )
            
            # Load credentials with write scope
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Build service
            self._service = build('sheets', 'v4', credentials=credentials)
            self.logger.info("Google Sheets Writer service initialized successfully")
            
        except Exception as e:
            raise GoogleSheetsWriterError(f"Failed to initialize Google Sheets Writer: {e}")
    
    def create_new_spreadsheet(self, title: str) -> str:
        """
        Create a new Google Spreadsheet.
        
        Args:
            title: Title for the new spreadsheet
            
        Returns:
            Spreadsheet ID
        """
        self._initialize_service()
        
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            result = self._service.spreadsheets().create(
                body=spreadsheet
            ).execute()
            
            spreadsheet_id = result['spreadsheetId']
            self.logger.info(f"Created new spreadsheet: {spreadsheet_id}")
            
            return spreadsheet_id
            
        except Exception as e:
            raise GoogleSheetsWriterError(f"Failed to create spreadsheet: {e}")
    
    def write_compliance_report(
        self,
        spreadsheet_id: str,
        report_data: Dict[str, Any],
        sheet_name: str = "Compliance Report"
    ) -> bool:
        """
        Write compliance report to Google Sheets.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            report_data: Compliance report data
            sheet_name: Name for the sheet
            
        Returns:
            True if successful
        """
        self._initialize_service()
        
        try:
            # Create new sheet
            self._create_sheet(spreadsheet_id, sheet_name)
            
            # Prepare header
            headers = [
                ["AI-POWERED COMPLIANCE CHECKER - DETAILED REPORT"],
                ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                [""],
                ["OVERALL COMPLIANCE SUMMARY"],
                []
            ]
            
            # Overall scores
            overall_data = [
                ["Overall Compliance Score", f"{report_data.get('overall_score', 0):.1f}%"],
                ["Total Clauses Analyzed", str(report_data.get('total_clauses', 0))],
                ["Compliant Clauses", str(report_data.get('compliant_count', 0))],
                ["Non-Compliant Clauses", str(report_data.get('non_compliant_count', 0))],
                ["High Risk Items", str(report_data.get('high_risk_count', 0))],
                [""],
                ["FRAMEWORK SCORES"],
                []
            ]
            
            # Framework scores
            framework_data = [["Framework", "Score", "Status"]]
            for framework, score in report_data.get('framework_scores', {}).items():
                status = "✓ Compliant" if score >= 75 else "✗ Non-Compliant"
                framework_data.append([framework, f"{score:.1f}%", status])
            
            framework_data.append([])
            framework_data.append(["DETAILED CLAUSE ANALYSIS"])
            framework_data.append([])
            
            # Clause headers
            clause_headers = [
                ["Clause ID", "Type", "Risk Level", "Compliance Status", "Frameworks", "Issues", "Recommendations"]
            ]
            
            # Clause details
            clause_data = []
            for clause in report_data.get('clauses', []):
                clause_data.append([
                    clause.get('id', ''),
                    clause.get('type', ''),
                    clause.get('risk_level', ''),
                    clause.get('status', ''),
                    ', '.join(clause.get('frameworks', [])),
                    '; '.join(clause.get('issues', []))[:200],  # Truncate if too long
                    '; '.join(clause.get('recommendations', []))[:200]
                ])
            
            # Combine all data
            all_data = headers + overall_data + framework_data + clause_headers + clause_data
            
            # Write to sheet
            self._write_data(spreadsheet_id, sheet_name, all_data)
            
            # Format the sheet
            self._format_report_sheet(spreadsheet_id, sheet_name, len(all_data))
            
            self.logger.info(f"Successfully wrote compliance report to sheet '{sheet_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write compliance report: {e}")
            raise GoogleSheetsWriterError(f"Failed to write compliance report: {e}")
    
    def write_missing_requirements(
        self,
        spreadsheet_id: str,
        missing_requirements: List[Dict[str, Any]],
        sheet_name: str = "Missing Requirements"
    ) -> bool:
        """
        Write missing requirements to Google Sheets.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            missing_requirements: List of missing requirements
            sheet_name: Name for the sheet
            
        Returns:
            True if successful
        """
        self._initialize_service()
        
        try:
            # Create new sheet
            self._create_sheet(spreadsheet_id, sheet_name)
            
            # Prepare data
            data = [
                ["MISSING COMPLIANCE REQUIREMENTS"],
                ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                [""],
                ["Framework", "Requirement ID", "Category", "Description", "Priority", "Recommended Action"],
                []
            ]
            
            for req in missing_requirements:
                data.append([
                    req.get('framework', ''),
                    req.get('requirement_id', ''),
                    req.get('category', ''),
                    req.get('description', '')[:200],
                    req.get('priority', ''),
                    req.get('recommendation', '')[:200]
                ])
            
            # Write to sheet
            self._write_data(spreadsheet_id, sheet_name, data)
            
            # Format the sheet
            self._format_requirements_sheet(spreadsheet_id, sheet_name, len(data))
            
            self.logger.info(f"Successfully wrote missing requirements to sheet '{sheet_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write missing requirements: {e}")
            raise GoogleSheetsWriterError(f"Failed to write missing requirements: {e}")
    
    def _create_sheet(self, spreadsheet_id: str, sheet_name: str):
        """Create a new sheet in the spreadsheet."""
        try:
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            
            self._service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()
            
        except Exception as e:
            # Sheet might already exist, that's okay
            self.logger.debug(f"Sheet creation note: {e}")
    
    def _write_data(self, spreadsheet_id: str, sheet_name: str, data: List[List[Any]]):
        """Write data to sheet."""
        try:
            range_name = f"{sheet_name}!A1"
            
            body = {
                'values': data
            }
            
            self._service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
        except Exception as e:
            raise GoogleSheetsWriterError(f"Failed to write data: {e}")
    
    def _format_report_sheet(self, spreadsheet_id: str, sheet_name: str, row_count: int):
        """Format the compliance report sheet."""
        try:
            # Get sheet ID
            sheet_metadata = self._service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            sheet_id = None
            for sheet in sheet_metadata['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is None:
                return
            
            # Format requests
            requests = [
                # Bold header row
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True,
                                    'fontSize': 14
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat'
                    }
                },
                # Auto-resize columns
                {
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 7
                        }
                    }
                },
                # Freeze header row
                {
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': sheet_id,
                            'gridProperties': {
                                'frozenRowCount': 1
                            }
                        },
                        'fields': 'gridProperties.frozenRowCount'
                    }
                }
            ]
            
            self._service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        except Exception as e:
            self.logger.debug(f"Formatting note: {e}")
    
    def _format_requirements_sheet(self, spreadsheet_id: str, sheet_name: str, row_count: int):
        """Format the missing requirements sheet."""
        self._format_report_sheet(spreadsheet_id, sheet_name, row_count)
    
    def append_notification(
        self,
        spreadsheet_id: str,
        notification: Dict[str, Any],
        sheet_name: str = "Notifications"
    ) -> bool:
        """
        Append a notification to the notifications sheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            notification: Notification data
            sheet_name: Name for the notifications sheet
            
        Returns:
            True if successful
        """
        self._initialize_service()
        
        try:
            # Ensure sheet exists
            self._create_sheet(spreadsheet_id, sheet_name)
            
            # Prepare notification row
            notification_row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                notification.get('type', ''),
                notification.get('severity', ''),
                notification.get('framework', ''),
                notification.get('message', ''),
                notification.get('details', '')
            ]
            
            # Append to sheet
            range_name = f"{sheet_name}!A:F"
            
            body = {
                'values': [notification_row]
            }
            
            self._service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            self.logger.info(f"Notification appended to sheet '{sheet_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to append notification: {e}")
            return False
