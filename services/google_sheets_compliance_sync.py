"""
Enhanced Google Sheets Integration Service
Supports bi-directional sync for compliance data
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class GoogleSheetsComplianceSync:
    """
    Service for bi-directional sync of compliance data with Google Sheets.
    Reads contract metadata and writes compliance status updates.
    """
    
    def __init__(self, credentials_path: Optional[str] = None, spreadsheet_id: Optional[str] = None):
        """
        Initialize Google Sheets compliance sync service.
        
        Args:
            credentials_path: Path to Google API credentials JSON file
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.logger = logging.getLogger(__name__)
        self.credentials_path = credentials_path or os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        self.spreadsheet_id = spreadsheet_id or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self.compliance_tab = os.getenv('GOOGLE_SHEETS_COMPLIANCE_TAB', 'Compliance_Status')
        self._service = None
        
        if not self.credentials_path:
            self.logger.warning("Google Sheets credentials path not configured")
        if not self.spreadsheet_id:
            self.logger.warning("Google Sheets spreadsheet ID not configured")
    
    def is_enabled(self) -> bool:
        """Check if Google Sheets integration is enabled."""
        return bool(self.credentials_path and self.spreadsheet_id)
    
    def _initialize_service(self):
        """Initialize Google Sheets API service."""
        if self._service is not None:
            return
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            if not Path(self.credentials_path).exists():
                raise Exception(f"Credentials file not found: {self.credentials_path}")
            
            # Load credentials with read/write scope
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            self._service = build('sheets', 'v4', credentials=credentials)
            self.logger.info("Google Sheets service initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets: {e}")
            raise
    
    def read_contract_metadata(self, sheet_name: str = "Contracts") -> List[Dict[str, Any]]:
        """
        Read contract metadata from Google Sheets master list.
        
        Args:
            sheet_name: Name of the sheet containing contract metadata
            
        Returns:
            List of contract metadata dictionaries
        """
        if not self.is_enabled():
            self.logger.warning("Google Sheets not configured")
            return []
        
        try:
            self._initialize_service()
            
            # Read data from sheet
            result = self._service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:Z"
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                self.logger.warning("No data found in sheet")
                return []
            
            # First row is headers
            headers = values[0]
            contracts = []
            
            # Process each row
            for row in values[1:]:
                # Pad row to match headers length
                row = row + [''] * (len(headers) - len(row))
                
                contract = {}
                for i, header in enumerate(headers):
                    contract[header.lower().replace(' ', '_')] = row[i] if i < len(row) else ''
                
                contracts.append(contract)
            
            self.logger.info(f"Read {len(contracts)} contracts from Google Sheets")
            return contracts
            
        except Exception as e:
            self.logger.error(f"Error reading from Google Sheets: {e}")
            return []
    
    def write_compliance_status(
        self,
        contract_name: str,
        compliance_data: Dict[str, Any]
    ) -> bool:
        """
        Write compliance status update to Google Sheets.
        
        Args:
            contract_name: Name of the contract
            compliance_data: Dictionary with compliance information
            
        Returns:
            True if successful
        """
        if not self.is_enabled():
            self.logger.warning("Google Sheets not configured")
            return False
        
        try:
            self._initialize_service()
            
            # Prepare row data
            row_data = [
                contract_name,
                compliance_data.get('risk_score', 0),
                compliance_data.get('compliance_status', 'Unknown'),
                compliance_data.get('frameworks_checked', ''),
                compliance_data.get('issues_found', 0),
                compliance_data.get('high_risk_issues', 0),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                compliance_data.get('recommendations', '')
            ]
            
            # Check if tab exists, create if not
            self._ensure_compliance_tab_exists()
            
            # Find or create row for this contract
            row_index = self._find_contract_row(contract_name)
            
            if row_index:
                # Update existing row
                range_name = f"{self.compliance_tab}!A{row_index}:H{row_index}"
                self._service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [row_data]}
                ).execute()
                self.logger.info(f"Updated compliance status for {contract_name}")
            else:
                # Append new row
                range_name = f"{self.compliance_tab}!A:H"
                self._service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [row_data]}
                ).execute()
                self.logger.info(f"Added new compliance status for {contract_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing to Google Sheets: {e}")
            return False
    
    def write_batch_compliance_status(
        self,
        compliance_data_list: List[Dict[str, Any]]
    ) -> bool:
        """
        Write multiple compliance status updates to Google Sheets.
        
        Args:
            compliance_data_list: List of compliance data dictionaries
            
        Returns:
            True if successful
        """
        if not self.is_enabled():
            self.logger.warning("Google Sheets not configured")
            return False
        
        try:
            self._initialize_service()
            
            # Ensure tab exists
            self._ensure_compliance_tab_exists()
            
            # Prepare batch data
            rows = []
            for data in compliance_data_list:
                row = [
                    data.get('contract_name', ''),
                    data.get('risk_score', 0),
                    data.get('compliance_status', 'Unknown'),
                    data.get('frameworks_checked', ''),
                    data.get('issues_found', 0),
                    data.get('high_risk_issues', 0),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    data.get('recommendations', '')
                ]
                rows.append(row)
            
            # Clear existing data (except header)
            self._service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.compliance_tab}!A2:H"
            ).execute()
            
            # Write new data
            self._service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.compliance_tab}!A2:H",
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()
            
            self.logger.info(f"Wrote {len(rows)} compliance records to Google Sheets")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing batch to Google Sheets: {e}")
            return False
    
    def _ensure_compliance_tab_exists(self):
        """Ensure the compliance tab exists in the spreadsheet."""
        try:
            # Get spreadsheet metadata
            spreadsheet = self._service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            # Check if tab exists
            sheets = spreadsheet.get('sheets', [])
            tab_exists = any(
                sheet['properties']['title'] == self.compliance_tab
                for sheet in sheets
            )
            
            if not tab_exists:
                # Create tab
                requests = [{
                    'addSheet': {
                        'properties': {
                            'title': self.compliance_tab
                        }
                    }
                }]
                
                self._service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': requests}
                ).execute()
                
                # Add headers
                headers = [
                    'Contract Name',
                    'Risk Score',
                    'Compliance Status',
                    'Frameworks Checked',
                    'Issues Found',
                    'High Risk Issues',
                    'Last Checked',
                    'Recommendations'
                ]
                
                self._service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.compliance_tab}!A1:H1",
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
                
                # Format header row
                self._format_header_row()
                
                self.logger.info(f"Created {self.compliance_tab} tab")
            
        except Exception as e:
            self.logger.error(f"Error ensuring tab exists: {e}")
    
    def _format_header_row(self):
        """Format the header row with bold text and background color."""
        try:
            # Get sheet ID
            spreadsheet = self._service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            sheet_id = None
            
            for sheet in sheets:
                if sheet['properties']['title'] == self.compliance_tab:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is None:
                return
            
            # Format requests
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 0.2,
                                    'green': 0.4,
                                    'blue': 0.8
                                },
                                'textFormat': {
                                    'bold': True,
                                    'foregroundColor': {
                                        'red': 1.0,
                                        'green': 1.0,
                                        'blue': 1.0
                                    }
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                    }
                }
            ]
            
            self._service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        except Exception as e:
            self.logger.error(f"Error formatting header: {e}")
    
    def _find_contract_row(self, contract_name: str) -> Optional[int]:
        """
        Find the row number for a specific contract.
        
        Args:
            contract_name: Name of the contract
            
        Returns:
            Row number (1-indexed) or None if not found
        """
        try:
            result = self._service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.compliance_tab}!A:A"
            ).execute()
            
            values = result.get('values', [])
            
            for i, row in enumerate(values):
                if row and row[0] == contract_name:
                    return i + 1  # 1-indexed
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding contract row: {e}")
            return None
    
    def export_compliance_report(self) -> bool:
        """
        Export a formatted compliance report to a new sheet.
        
        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            self._initialize_service()
            
            # Create report sheet name
            report_name = f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Add new sheet
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': report_name
                    }
                }
            }]
            
            self._service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            self.logger.info(f"Created report sheet: {report_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting report: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize service
    sheets_sync = GoogleSheetsComplianceSync()
    
    if sheets_sync.is_enabled():
        # Write compliance status
        sheets_sync.write_compliance_status(
            contract_name="Data Processing Agreement - Acme Corp",
            compliance_data={
                'risk_score': 85.5,
                'compliance_status': 'Non-Compliant',
                'frameworks_checked': 'GDPR, HIPAA',
                'issues_found': 5,
                'high_risk_issues': 2,
                'recommendations': 'Add data processing clauses'
            }
        )
