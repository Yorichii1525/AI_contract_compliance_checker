"""
Real-time Regulatory Update Tracking Service.
Monitors regulatory sources, detects changes, and provides alerts.
"""
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from collections import defaultdict

from models.regulatory_update import (
    RegulatoryUpdate, RegulatorySource, UpdateType, UpdateSeverity, UpdateStatus, UpdateAlert
)
from services.serper_api_client import SerperAPIClient, OFFICIAL_SOURCES, DEFAULT_KEYWORDS
from services.groq_api_client import GroqAPIClient
from services.knowledge_base_loader import KnowledgeBaseLoader

import os
import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class RegulatoryUpdateTracker:
    """Main service for tracking and analyzing regulatory updates."""
    
    def __init__(
        self,
        serper_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        storage_dir: Optional[Path] = None
    ):
        """
        Initialize regulatory update tracker.
        
        Args:
            serper_api_key: Serper API key
            groq_api_key: Groq API key
            storage_dir: Directory for storing update history
        """
        self.serper = SerperAPIClient(api_key=serper_api_key)
        self.groq = GroqAPIClient(api_key=groq_api_key)
        self.knowledge_base = KnowledgeBaseLoader()
        
        self.storage_dir = storage_dir or Path(__file__).parent.parent / "data" / "regulatory_updates"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.updates_file = self.storage_dir / "updates.jsonl"
        self.sources_file = self.storage_dir / "sources.json"
        self.alerts_file = self.storage_dir / "alerts.json"
        
        # In-memory caches
        self.sources: Dict[str, RegulatorySource] = {}
        self.alerts: List[UpdateAlert] = []
        self.recent_updates: List[RegulatoryUpdate] = []
        
        # Statistics
        self.stats = defaultdict(int)
        
        logger.info("Initializing RegulatoryUpdateTracker...")
        self._load_sources()
        self._load_alerts()
        self._load_recent_updates()
        
        logger.info(f"Loaded {len(self.sources)} sources and {len(self.alerts)} alerts")
    
    def _load_sources(self):
        """Load configured sources from file."""
        if self.sources_file.exists():
            try:
                with open(self.sources_file, 'r') as f:
                    sources_data = json.load(f)
                    for source_dict in sources_data:
                        source = RegulatorySource(**source_dict)
                        self.sources[source.source_id] = source
                logger.info(f"Loaded {len(self.sources)} sources from file")
            except Exception as e:
                logger.error(f"Failed to load sources: {e}")
        else:
            # Initialize default sources
            self._initialize_default_sources()
    
    def _initialize_default_sources(self):
        """Create default regulatory sources."""
        logger.info("Initializing default regulatory sources...")
        
        for framework, domains in OFFICIAL_SOURCES.items():
            for domain in domains:
                source_id = f"{framework.lower()}_{domain.replace('.', '_')}"
                source = RegulatorySource(
                    source_id=source_id,
                    name=f"{framework} - {domain}",
                    url=f"https://{domain}",
                    framework=framework,
                    source_type="Official",
                    check_frequency_hours=24,
                    keywords=DEFAULT_KEYWORDS.get(framework, [])
                )
                self.sources[source_id] = source
        
        self._save_sources()
        logger.info(f"Initialized {len(self.sources)} default sources")
    
    def _save_sources(self):
        """Save sources to file."""
        try:
            sources_data = [source.to_dict() for source in self.sources.values()]
            with open(self.sources_file, 'w') as f:
                json.dump(sources_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save sources: {e}")
    
    def _load_alerts(self):
        """Load alert configurations from file."""
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, 'r') as f:
                    alerts_data = json.load(f)
                    for alert_dict in alerts_data:
                        alert = UpdateAlert(**alert_dict)
                        self.alerts.append(alert)
                logger.info(f"Loaded {len(self.alerts)} alerts from file")
            except Exception as e:
                logger.error(f"Failed to load alerts: {e}")
    
    def _save_alerts(self):
        """Save alert configurations to file."""
        try:
            alerts_data = [
                {
                    'alert_id': alert.alert_id,
                    'framework': alert.framework,
                    'keywords': alert.keywords,
                    'min_severity': alert.min_severity.value,
                    'notification_channels': alert.notification_channels,
                    'is_active': alert.is_active
                }
                for alert in self.alerts
            ]
            with open(self.alerts_file, 'w') as f:
                json.dump(alerts_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")
    
    def _load_recent_updates(self, days: int = 30):
        """Load recent updates from JSONL file."""
        if not self.updates_file.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        count = 0
        
        try:
            with open(self.updates_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        update = RegulatoryUpdate.from_dict(data)
                        
                        if update.detected_date >= cutoff_date:
                            self.recent_updates.append(update)
                            count += 1
                    except Exception as e:
                        logger.warning(f"Failed to parse update: {e}")
                        continue
            
            logger.info(f"Loaded {count} recent updates from last {days} days")
        except Exception as e:
            logger.error(f"Failed to load recent updates: {e}")
    
    def save_update(self, update: RegulatoryUpdate):
        """Save an update to JSONL file."""
        try:
            with open(self.updates_file, 'a') as f:
                f.write(update.to_jsonl() + '\n')
            
            self.recent_updates.append(update)
            self.stats['updates_saved'] += 1
            
            logger.info(f"Saved update: {update.update_id}")
        except Exception as e:
            logger.error(f"Failed to save update: {e}")
    
    def check_for_updates(
        self,
        framework: str,
        time_range: str = 'w',
        force_check: bool = False
    ) -> List[RegulatoryUpdate]:
        """
        Check for new regulatory updates for a framework.
        
        Args:
            framework: Framework to check (GDPR, HIPAA, CCPA, SOX)
            time_range: Time range to search ('d', 'w', 'm', 'y')
            force_check: Force check even if recently checked
        
        Returns:
            List of detected updates
        """
        logger.info(f"Checking for {framework} updates (time_range={time_range})")
        
        updates = []
        
        # Get sources for this framework
        framework_sources = [s for s in self.sources.values() if s.framework == framework and s.is_active]
        
        for source in framework_sources:
            # Check if we need to check this source
            if not force_check and source.last_checked:
                hours_since_check = (datetime.now() - source.last_checked).total_seconds() / 3600
                if hours_since_check < source.check_frequency_hours:
                    logger.debug(f"Skipping {source.name} - checked {hours_since_check:.1f}h ago")
                    continue
            
            # Search for updates
            try:
                search_results = self.serper.search_regulatory_updates(
                    framework=framework,
                    keywords=source.keywords,
                    num_results=10,
                    time_range=time_range
                )
                
                logger.info(f"Found {len(search_results)} results from {source.name}")
                
                # Process each result
                for result in search_results:
                    update = self._process_search_result(result, source, framework)
                    if update and not self._is_duplicate(update):
                        updates.append(update)
                
                # Update last checked time
                source.last_checked = datetime.now()
                
            except Exception as e:
                logger.error(f"Error checking source {source.name}: {e}")
                continue
        
        # Save updated sources
        self._save_sources()
        
        # Analyze updates with Groq
        for update in updates:
            try:
                analysis = self.groq.analyze_regulatory_text(
                    text=update.full_text,
                    framework=framework,
                    context=f"Source: {update.source.name}"
                )
                
                if 'error' not in analysis:
                    update.ai_analysis = json.dumps(analysis)
                    update.severity = UpdateSeverity(analysis.get('severity', 'Medium'))
                    update.impact_score = analysis.get('impact_score', 0.5)
                    update.required_actions = analysis.get('required_actions', [])
                
            except Exception as e:
                logger.error(f"Failed to analyze update with Groq: {e}")
        
        logger.info(f"Detected {len(updates)} new {framework} updates")
        
        # Save all new updates
        for update in updates:
            self.save_update(update)
        
        # Check alerts
        self._check_alerts(updates)
        
        self.stats['checks_performed'] += 1
        self.stats[f'{framework}_updates_found'] += len(updates)
        
        return updates
    
    def _process_search_result(
        self,
        result: Dict[str, Any],
        source: RegulatorySource,
        framework: str
    ) -> Optional[RegulatoryUpdate]:
        """Process a search result into a RegulatoryUpdate."""
        try:
            update_id = str(uuid.uuid4())
            
            title = result.get('title', 'Untitled')
            snippet = result.get('snippet', '')
            link = result.get('link', '')
            
            # Determine update type based on title/snippet
            update_type = self._classify_update_type(title + ' ' + snippet)
            
            # Initial severity (will be refined by AI)
            severity = UpdateSeverity.MEDIUM
            
            update = RegulatoryUpdate(
                update_id=update_id,
                framework=framework,
                title=title,
                summary=snippet,
                full_text=snippet,  # Will be expanded if we fetch full content
                source=source,
                update_type=update_type,
                severity=severity,
                status=UpdateStatus.DETECTED,
                detected_date=datetime.now(),
                source_url=link,
                keywords=source.keywords
            )
            
            return update
            
        except Exception as e:
            logger.error(f"Failed to process search result: {e}")
            return None
    
    def _classify_update_type(self, text: str) -> UpdateType:
        """Classify update type based on text."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['new regulation', 'new rule', 'enacted']):
            return UpdateType.NEW_REGULATION
        elif any(word in text_lower for word in ['amendment', 'amended', 'modified', 'revised']):
            return UpdateType.AMENDMENT
        elif any(word in text_lower for word in ['clarification', 'guidance', 'interpretation']):
            return UpdateType.CLARIFICATION
        elif any(word in text_lower for word in ['enforcement', 'fine', 'penalty', 'violation']):
            return UpdateType.ENFORCEMENT
        elif any(word in text_lower for word in ['guidance', 'guide', 'best practice']):
            return UpdateType.GUIDANCE
        elif any(word in text_lower for word in ['case', 'court', 'ruling', 'decision']):
            return UpdateType.CASE_LAW
        elif any(word in text_lower for word in ['proposed', 'proposal', 'draft']):
            return UpdateType.PROPOSAL
        else:
            return UpdateType.CLARIFICATION
    
    def _is_duplicate(self, update: RegulatoryUpdate) -> bool:
        """Check if update is a duplicate of existing update."""
        for existing in self.recent_updates:
            # Check if titles are very similar
            if existing.title == update.title and existing.framework == update.framework:
                return True
            
            # Check if source URLs match
            if update.source_url and existing.source_url == update.source_url:
                return True
        
        return False
    
    def _check_alerts(self, updates: List[RegulatoryUpdate]):
        """Check if any alerts should be triggered for updates."""
        for update in updates:
            for alert in self.alerts:
                if alert.matches_update(update):
                    logger.info(f"Alert triggered: {alert.alert_id} for update {update.update_id}")
                    # In a full implementation, send notifications here
                    update.status = UpdateStatus.NOTIFIED
    
    def check_all_frameworks(self, frameworks: Optional[List[str]] = None, time_range: str = 'w') -> Dict[str, List[RegulatoryUpdate]]:
        """
        Check all enabled frameworks for updates.
        
        Args:
            frameworks: List of frameworks to check (default: all frameworks)
            time_range: Time range to check
        
        Returns:
            Dictionary mapping framework to list of updates
        """
        results = {}
        
        # Use provided frameworks or default to all
        frameworks_to_check = frameworks or ['GDPR', 'HIPAA', 'CCPA', 'SOX']
        
        for framework in frameworks_to_check:
            logger.info(f"Checking {framework}...")
            updates = self.check_for_updates(framework, time_range=time_range)
            results[framework] = updates
        
        return results
    
    def get_updates(
        self,
        framework: Optional[str] = None,
        severity: Optional[UpdateSeverity] = None,
        status: Optional[UpdateStatus] = None,
        days: int = 30,
        limit: Optional[int] = None
    ) -> List[RegulatoryUpdate]:
        """
        Get filtered list of updates.
        
        Args:
            framework: Filter by framework
            severity: Filter by minimum severity
            status: Filter by status
            days: Get updates from last N days
            limit: Maximum number of results
        
        Returns:
            Filtered list of updates
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered = []
        for update in self.recent_updates:
            if update.detected_date < cutoff_date:
                continue
            
            if framework and update.framework != framework:
                continue
            
            if severity:
                severity_order = {
                    UpdateSeverity.LOW: 0,
                    UpdateSeverity.MEDIUM: 1,
                    UpdateSeverity.HIGH: 2,
                    UpdateSeverity.CRITICAL: 3
                }
                if severity_order[update.severity] < severity_order[severity]:
                    continue
            
            if status and update.status != status:
                continue
            
            filtered.append(update)
        
        # Sort by detected date (newest first)
        filtered.sort(key=lambda x: x.detected_date, reverse=True)
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tracking statistics."""
        framework_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        status_counts = defaultdict(int)
        
        for update in self.recent_updates:
            framework_counts[update.framework] += 1
            severity_counts[update.severity.value] += 1
            status_counts[update.status.value] += 1
        
        return {
            'total_sources': len(self.sources),
            'active_sources': sum(1 for s in self.sources.values() if s.is_active),
            'total_alerts': len(self.alerts),
            'active_alerts': sum(1 for a in self.alerts if a.is_active),
            'recent_updates': len(self.recent_updates),
            'by_framework': dict(framework_counts),
            'by_severity': dict(severity_counts),
            'by_status': dict(status_counts),
            'checks_performed': self.stats.get('checks_performed', 0),
            'updates_saved': self.stats.get('updates_saved', 0)
        }
    """
    Service for tracking regulatory updates from various sources.
    Monitors SEC Edgar, EUR-Lex, and other regulatory APIs.
    """
    
    def __init__(self):
        """Initialize regulatory update tracker."""
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(__file__).parent.parent / "data" / "regulatory_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # API configurations
        self.sec_edgar_url = os.getenv('SEC_EDGAR_API_URL', 'https://www.sec.gov/cgi-bin/browse-edgar')
        self.user_agent = os.getenv('REGULATORY_USER_AGENT', 'ComplianceBot/1.0')
        self.polling_interval_hours = int(os.getenv('POLLING_INTERVAL_HOURS', '24'))
        
        # Track last update times
        self.last_check_file = self.cache_dir / "last_check.json"
        self.last_checks = self._load_last_checks()
    
    def _load_last_checks(self) -> Dict[str, str]:
        """Load last check timestamps."""
        if self.last_check_file.exists():
            try:
                with open(self.last_check_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading last checks: {e}")
        return {}
    
    def _save_last_checks(self):
        """Save last check timestamps."""
        try:
            with open(self.last_check_file, 'w') as f:
                json.dump(self.last_checks, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving last checks: {e}")
    
    def should_check_source(self, source: str) -> bool:
        """
        Check if enough time has passed since last check for a source.
        
        Args:
            source: Source identifier
            
        Returns:
            True if should check now
        """
        if source not in self.last_checks:
            return True
        
        last_check = datetime.fromisoformat(self.last_checks[source])
        hours_since = (datetime.now() - last_check).total_seconds() / 3600
        
        return hours_since >= self.polling_interval_hours
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for change detection."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def fetch_sec_edgar_updates(
        self,
        company: Optional[str] = None,
        form_type: str = '10-K',
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch updates from SEC Edgar.
        
        Args:
            company: Company ticker or CIK (optional)
            form_type: Type of SEC form to monitor
            days_back: Number of days to look back
            
        Returns:
            List of regulatory updates
        """
        if not self.should_check_source('sec_edgar'):
            self.logger.info("Skipping SEC Edgar check (too recent)")
            return []
        
        try:
            self.logger.info(f"Fetching SEC Edgar updates (form: {form_type}, days: {days_back})")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Build request parameters
            params = {
                'action': 'getcompany',
                'type': form_type,
                'dateb': end_date.strftime('%Y%m%d'),
                'datea': start_date.strftime('%Y%m%d'),
                'output': 'atom',
                'count': 100
            }
            
            if company:
                params['CIK'] = company
            
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/atom+xml'
            }
            
            # Make request
            response = requests.get(
                self.sec_edgar_url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                # Parse response (simplified - real implementation would parse XML)
                updates = self._parse_sec_edgar_response(response.text)
                
                # Update last check time
                self.last_checks['sec_edgar'] = datetime.now().isoformat()
                self._save_last_checks()
                
                self.logger.info(f"Found {len(updates)} SEC Edgar updates")
                return updates
            else:
                self.logger.error(f"SEC Edgar API error: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching SEC Edgar updates: {e}")
            return []
    
    def _parse_sec_edgar_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse SEC Edgar XML response.
        
        Args:
            xml_content: XML content from SEC Edgar
            
        Returns:
            List of parsed updates
        """
        # Simplified parsing - real implementation would use XML parser
        updates = []
        
        try:
            # This is a placeholder - implement proper XML parsing
            updates.append({
                'source': 'SEC Edgar',
                'title': 'Sample SEC Filing Update',
                'description': 'New regulatory filing detected',
                'url': 'https://www.sec.gov/edgar',
                'published_date': datetime.now().isoformat(),
                'severity': 'medium',
                'jurisdiction': 'US',
                'applicable_domain': 'Finance'
            })
        except Exception as e:
            self.logger.error(f"Error parsing SEC Edgar response: {e}")
        
        return updates
    
    def fetch_gdpr_updates(self) -> List[Dict[str, Any]]:
        """
        Fetch GDPR-related updates from EUR-Lex.
        
        Returns:
            List of regulatory updates
        """
        if not self.should_check_source('eur_lex'):
            self.logger.info("Skipping EUR-Lex check (too recent)")
            return []
        
        try:
            self.logger.info("Fetching EUR-Lex GDPR updates")
            
            # EUR-Lex API endpoint (example)
            url = "https://eur-lex.europa.eu/search.html"
            params = {
                'qid': '1234567890',
                'DTS_DOM': 'ALL',
                'type': 'advanced',
                'lang': 'en',
                'SUBDOM_INIT': 'EU_LAW',
                'DTS_SUBDOM': 'EU_LAW'
            }
            
            headers = {
                'User-Agent': self.user_agent
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                updates = self._parse_eur_lex_response(response.text)
                
                # Update last check time
                self.last_checks['eur_lex'] = datetime.now().isoformat()
                self._save_last_checks()
                
                self.logger.info(f"Found {len(updates)} EUR-Lex updates")
                return updates
            else:
                self.logger.error(f"EUR-Lex API error: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching EUR-Lex updates: {e}")
            return []
    
    def _parse_eur_lex_response(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse EUR-Lex HTML response.
        
        Args:
            html_content: HTML content from EUR-Lex
            
        Returns:
            List of parsed updates
        """
        # Placeholder - implement proper HTML parsing
        updates = []
        
        updates.append({
            'source': 'EUR-Lex',
            'title': 'Sample GDPR Amendment',
            'description': 'Updated data processing requirements',
            'url': 'https://eur-lex.europa.eu',
            'published_date': datetime.now().isoformat(),
            'severity': 'high',
            'jurisdiction': 'EU',
            'applicable_domain': 'GDPR'
        })
        
        return updates
    
    def fetch_all_updates(self) -> List[Dict[str, Any]]:
        """
        Fetch updates from all configured sources.
        
        Returns:
            Combined list of regulatory updates
        """
        all_updates = []
        
        # Fetch from SEC Edgar
        sec_updates = self.fetch_sec_edgar_updates()
        all_updates.extend(sec_updates)
        
        # Fetch from EUR-Lex
        gdpr_updates = self.fetch_gdpr_updates()
        all_updates.extend(gdpr_updates)
        
        # Add more sources as needed
        # hipaa_updates = self.fetch_hipaa_updates()
        # all_updates.extend(hipaa_updates)
        
        return all_updates
    
    def extract_keywords_from_update(self, update: Dict[str, Any]) -> List[str]:
        """
        Extract relevant keywords from regulatory update using NLP.
        
        Args:
            update: Regulatory update dictionary
            
        Returns:
            List of extracted keywords
        """
        try:
            # Try to use spaCy if available
            import spacy
            
            # Load English model
            try:
                nlp = spacy.load("en_core_web_sm")
            except:
                self.logger.warning("spaCy model not found. Using simple keyword extraction.")
                return self._simple_keyword_extraction(update)
            
            # Combine title and description
            text = f"{update.get('title', '')} {update.get('description', '')}"
            
            # Process text
            doc = nlp(text)
            
            # Extract entities and key phrases
            keywords = []
            
            # Add named entities
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'LAW', 'GPE', 'PRODUCT']:
                    keywords.append(ent.text.lower())
            
            # Add important nouns and noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3:  # Limit phrase length
                    keywords.append(chunk.text.lower())
            
            # Remove duplicates and return
            return list(set(keywords))[:20]  # Limit to top 20
            
        except ImportError:
            self.logger.info("spaCy not available, using simple keyword extraction")
            return self._simple_keyword_extraction(update)
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return self._simple_keyword_extraction(update)
    
    def _simple_keyword_extraction(self, update: Dict[str, Any]) -> List[str]:
        """
        Simple keyword extraction without NLP.
        
        Args:
            update: Regulatory update dictionary
            
        Returns:
            List of keywords
        """
        text = f"{update.get('title', '')} {update.get('description', '')}".lower()
        
        # Common legal/compliance keywords
        legal_terms = [
            'data', 'privacy', 'protection', 'security', 'consent', 'processing',
            'controller', 'processor', 'breach', 'notification', 'rights', 'subject',
            'transfer', 'compliance', 'audit', 'liability', 'penalty', 'regulation',
            'directive', 'law', 'requirement', 'obligation', 'contract', 'agreement'
        ]
        
        # Extract matching terms
        keywords = [term for term in legal_terms if term in text]
        
        return keywords[:10]
    
    def calculate_urgency_score(self, update: Dict[str, Any]) -> float:
        """
        Calculate modification urgency score for a regulatory update.
        
        Args:
            update: Regulatory update dictionary
            
        Returns:
            Urgency score (0-100)
        """
        score = 0.0
        
        # Base score on severity
        severity = update.get('severity', 'medium').lower()
        severity_scores = {
            'critical': 100,
            'high': 80,
            'medium': 50,
            'low': 20
        }
        score += severity_scores.get(severity, 50)
        
        # Adjust for recency
        try:
            published = datetime.fromisoformat(update.get('published_date', datetime.now().isoformat()))
            days_old = (datetime.now() - published).days
            
            if days_old <= 7:
                score += 10
            elif days_old <= 30:
                score += 5
        except:
            pass
        
        # Adjust for jurisdiction importance
        jurisdiction = update.get('jurisdiction', '').upper()
        if jurisdiction in ['EU', 'US']:
            score += 5
        
        # Cap at 100
        return min(score, 100.0)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize tracker
    tracker = RegulatoryUpdateTracker()
    
    # Fetch updates
    updates = tracker.fetch_all_updates()
    
    # Process each update
    for update in updates:
        print(f"\nRegulatory Update: {update['title']}")
        print(f"Source: {update['source']}")
        print(f"Severity: {update['severity']}")
        
        # Extract keywords
        keywords = tracker.extract_keywords_from_update(update)
        print(f"Keywords: {', '.join(keywords[:5])}")
        
        # Calculate urgency
        urgency = tracker.calculate_urgency_score(update)
        print(f"Urgency Score: {urgency:.1f}/100")
