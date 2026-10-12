"""
Multi-Platform Integration Orchestrator
Coordinates all integration services for automated compliance workflow
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

# Import all integration services
from services.slack_notification_service import SlackNotificationService
from services.email_notification_service import EmailNotificationService
from services.google_sheets_compliance_sync import GoogleSheetsComplianceSync
from services.regulatory_update_tracker import RegulatoryUpdateTracker
from services.contract_modification_engine import ContractModificationEngine

logger = logging.getLogger(__name__)


class ComplianceIntegrationOrchestrator:
    """
    Orchestrates all multi-platform integrations for the compliance system.
    Manages workflow between regulatory tracking, contract analysis, and notifications.
    """
    
    def __init__(self):
        """Initialize all integration services."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.slack = SlackNotificationService()
        self.email = EmailNotificationService()
        self.sheets = GoogleSheetsComplianceSync()
        self.regulatory_tracker = RegulatoryUpdateTracker()
        self.modification_engine = ContractModificationEngine()
        
        self.logger.info("Compliance Integration Orchestrator initialized")
    
    def run_daily_compliance_check(
        self,
        contracts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run daily compliance check workflow.
        
        Args:
            contracts: List of contract dictionaries to check
            
        Returns:
            Summary of compliance check results
        """
        self.logger.info(f"Starting daily compliance check for {len(contracts)} contracts")
        
        results = {
            'total_contracts': len(contracts),
            'high_risk_contracts': [],
            'expiring_contracts': [],
            'regulatory_updates': [],
            'amendments_generated': [],
            'notifications_sent': 0
        }
        
        # 1. Check for regulatory updates
        regulatory_updates = self.regulatory_tracker.fetch_all_updates()
        results['regulatory_updates'] = regulatory_updates
        
        if regulatory_updates:
            self.logger.info(f"Found {len(regulatory_updates)} regulatory updates")
            
            # Notify about critical updates
            for update in regulatory_updates:
                if update.get('severity') in ['critical', 'high']:
                    self.slack.notify_regulatory_update(
                        regulation_title=update['title'],
                        jurisdiction=update['jurisdiction'],
                        severity=update['severity'],
                        affected_contracts=len(contracts),  # Estimate
                        summary=update['description']
                    )
                    results['notifications_sent'] += 1
        
        # 2. Process each contract
        compliance_data_list = []
        
        for contract in contracts:
            contract_result = self._process_single_contract(contract, regulatory_updates)
            
            # Track high-risk contracts
            if contract_result['risk_score'] >= 80:
                results['high_risk_contracts'].append(contract_result)
                
                # Send alert
                self.slack.notify_high_risk_contract(
                    contract_name=contract['name'],
                    risk_score=contract_result['risk_score'],
                    compliance_issues=contract_result['compliance_issues']
                )
                results['notifications_sent'] += 1
            
            # Track expiring contracts
            if contract_result.get('days_until_expiry') and contract_result['days_until_expiry'] <= 30:
                results['expiring_contracts'].append(contract_result)
                
                # Send expiry warning
                self.slack.notify_contract_expiring(
                    contract_name=contract['name'],
                    days_until_expiry=contract_result['days_until_expiry'],
                    expiry_date=contract.get('expiry_date', 'Unknown')
                )
                results['notifications_sent'] += 1
            
            # Collect for Google Sheets
            compliance_data_list.append({
                'contract_name': contract['name'],
                'risk_score': contract_result['risk_score'],
                'compliance_status': contract_result['compliance_status'],
                'frameworks_checked': ', '.join(contract_result.get('frameworks', [])),
                'issues_found': len(contract_result['compliance_issues']),
                'high_risk_issues': len([i for i in contract_result['compliance_issues'] if i.get('severity') == 'high']),
                'recommendations': contract_result.get('recommendations_summary', '')
            })
        
        # 3. Update Google Sheets
        if self.sheets.is_enabled() and compliance_data_list:
            success = self.sheets.write_batch_compliance_status(compliance_data_list)
            if success:
                self.logger.info("Updated Google Sheets with compliance data")
        
        # 4. Generate amendments for regulatory updates
        if regulatory_updates:
            for update in regulatory_updates:
                amendments = self._generate_amendments_for_update(update, contracts)
                results['amendments_generated'].extend(amendments)
        
        # 5. Send summary report
        self._send_daily_summary_email(results)
        
        self.logger.info("Daily compliance check completed")
        return results
    
    def _process_single_contract(
        self,
        contract: Dict[str, Any],
        regulatory_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a single contract for compliance.
        
        Args:
            contract: Contract dictionary
            regulatory_updates: List of recent regulatory updates
            
        Returns:
            Contract compliance result
        """
        result = {
            'name': contract['name'],
            'risk_score': contract.get('risk_score', 50),
            'compliance_status': contract.get('compliance_status', 'pending'),
            'compliance_issues': contract.get('compliance_issues', []),
            'frameworks': contract.get('frameworks', ['GDPR']),
            'days_until_expiry': self._calculate_days_until_expiry(contract.get('expiry_date'))
        }
        
        # Check if any new regulations affect this contract
        affected_by_updates = []
        for update in regulatory_updates:
            # Simple check - can be enhanced with NLP
            if self._contract_affected_by_regulation(contract, update):
                affected_by_updates.append(update['title'])
        
        if affected_by_updates:
            result['affected_by_regulations'] = affected_by_updates
            result['recommendations_summary'] = f"Review against: {', '.join(affected_by_updates[:2])}"
        
        return result
    
    def _calculate_days_until_expiry(self, expiry_date: Optional[str]) -> Optional[int]:
        """Calculate days until contract expiration."""
        if not expiry_date:
            return None
        
        try:
            expiry = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
            delta = expiry - datetime.now()
            return delta.days
        except:
            return None
    
    def _contract_affected_by_regulation(
        self,
        contract: Dict[str, Any],
        regulation: Dict[str, Any]
    ) -> bool:
        """Check if a contract is affected by a regulation."""
        # Simple heuristic - can be enhanced
        contract_domains = set(contract.get('applicable_domains', []))
        reg_domain = regulation.get('applicable_domain', '')
        
        return reg_domain in contract_domains
    
    def _generate_amendments_for_update(
        self,
        regulation: Dict[str, Any],
        contracts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate amendments for contracts affected by a regulatory update.
        
        Args:
            regulation: Regulatory update
            contracts: List of contracts
            
        Returns:
            List of generated amendments
        """
        amendments = []
        
        for contract in contracts:
            # Check if contract is affected
            if not self._contract_affected_by_regulation(contract, regulation):
                continue
            
            # Get contract clauses (simplified - would come from database)
            clauses = contract.get('clauses', [])
            
            # Map regulation to clauses
            mappings = self.modification_engine.map_regulation_to_clauses(
                regulation=regulation,
                contract_clauses=clauses
            )
            
            # Generate amendments for mapped clauses
            for mapping in mappings[:3]:  # Limit to top 3
                clause = {
                    'id': mapping['clause_id'],
                    'clause_number': mapping['clause_number'],
                    'clause_title': mapping['clause_title'],
                    'clause_text': mapping['clause_text'],
                    'clause_type': mapping['clause_type']
                }
                
                amendment = self.modification_engine.generate_amendment_suggestion(
                    clause=clause,
                    regulation=regulation,
                    use_ai=False  # Set to True if OpenAI is configured
                )
                
                # Save amendment
                self.modification_engine.save_amendment(amendment)
                amendments.append(amendment)
                
                # Send email to legal team if high priority
                if regulation.get('severity') in ['critical', 'high']:
                    self.email.send_amendment_suggestions(
                        contract_name=contract['name'],
                        amendments=[amendment]
                    )
        
        return amendments
    
    def _send_daily_summary_email(self, results: Dict[str, Any]):
        """Send daily summary email to legal team."""
        if not self.email:
            return
        
        summary = {
            'total_contracts': results['total_contracts'],
            'compliant_contracts': results['total_contracts'] - len(results['high_risk_contracts']),
            'non_compliant_contracts': len(results['high_risk_contracts'])
        }
        
        self.email.send_compliance_report(
            report_summary=summary
        )
    
    def process_uploaded_contract(
        self,
        contract_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> bool:
        """
        Process a newly uploaded contract through all integrations.
        
        Args:
            contract_data: Contract metadata
            analysis_results: Results from compliance analysis
            
        Returns:
            True if processed successfully
        """
        try:
            contract_name = contract_data.get('name', 'Unknown Contract')
            risk_score = analysis_results.get('risk_score', 0)
            
            # 1. Send Slack notification if high risk
            if risk_score >= 80:
                self.slack.notify_high_risk_contract(
                    contract_name=contract_name,
                    risk_score=risk_score,
                    compliance_issues=analysis_results.get('compliance_issues', [])
                )
            
            # 2. Update Google Sheets
            if self.sheets.is_enabled():
                self.sheets.write_compliance_status(
                    contract_name=contract_name,
                    compliance_data={
                        'risk_score': risk_score,
                        'compliance_status': analysis_results.get('compliance_status', 'Unknown'),
                        'frameworks_checked': ', '.join(analysis_results.get('frameworks', [])),
                        'issues_found': len(analysis_results.get('compliance_issues', [])),
                        'high_risk_issues': len([i for i in analysis_results.get('compliance_issues', []) if i.get('severity') == 'high']),
                        'recommendations': analysis_results.get('recommendations_summary', '')
                    }
                )
            
            # 3. Send email if critical issues found
            high_risk_issues = [i for i in analysis_results.get('compliance_issues', []) if i.get('severity') == 'high']
            if len(high_risk_issues) >= 3:
                self.email.send_high_risk_alert(
                    contract_name=contract_name,
                    risk_score=risk_score,
                    compliance_issues=high_risk_issues,
                    recommendations=analysis_results.get('recommendations', [])
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing uploaded contract: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize orchestrator
    orchestrator = ComplianceIntegrationOrchestrator()
    
    # Sample contract data
    sample_contracts = [
        {
            'name': 'Data Processing Agreement - Acme Corp',
            'risk_score': 85,
            'compliance_status': 'non_compliant',
            'compliance_issues': [
                {'severity': 'high', 'description': 'Missing GDPR Article 28 clauses'},
                {'severity': 'high', 'description': 'Inadequate security measures'}
            ],
            'frameworks': ['GDPR', 'CCPA'],
            'applicable_domains': ['GDPR', 'Privacy'],
            'expiry_date': '2025-12-31',
            'clauses': []
        }
    ]
    
    # Run daily check
    results = orchestrator.run_daily_compliance_check(sample_contracts)
    
    print("\nDaily Compliance Check Results:")
    print(f"Total Contracts: {results['total_contracts']}")
    print(f"High Risk: {len(results['high_risk_contracts'])}")
    print(f"Expiring Soon: {len(results['expiring_contracts'])}")
    print(f"Regulatory Updates: {len(results['regulatory_updates'])}")
    print(f"Amendments Generated: {len(results['amendments_generated'])}")
    print(f"Notifications Sent: {results['notifications_sent']}")
