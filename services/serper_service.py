"""Serper API Service - Web search for regulatory updates and compliance information."""

import logging
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SerperError(Exception):
    """Base exception for Serper API errors."""
    pass


class SerperService:
    """Service for searching regulatory information using Serper API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Serper service.
        
        Args:
            api_key: Serper API key (or set SERPER_API_KEY env variable)
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key or os.getenv('SERPER_API_KEY')
        
        if not self.api_key:
            self.logger.warning(
                "Serper API key not found. Set SERPER_API_KEY environment variable. "
                "Get your key from https://serper.dev"
            )
        
        self.base_url = "https://google.serper.dev/search"
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search"
    ) -> Dict[str, Any]:
        """
        Perform a search using Serper API.
        
        Args:
            query: Search query
            num_results: Number of results to return
            search_type: Type of search ('search', 'news', 'images')
            
        Returns:
            Search results
        """
        if not self.api_key:
            raise SerperError("Serper API key not configured")
        
        try:
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': query,
                'num': num_results
            }
            
            # Use appropriate endpoint
            url = self.base_url
            if search_type == 'news':
                url = "https://google.serper.dev/news"
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            results = response.json()
            
            self.logger.info(f"Search completed: {query} ({len(results.get('organic', []))} results)")
            
            return results
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Serper API request failed: {e}")
            raise SerperError(f"Search request failed: {e}")
        except Exception as e:
            self.logger.error(f"Serper search error: {e}")
            raise SerperError(f"Search error: {e}")
    
    def search_regulatory_updates(
        self,
        framework: str,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for regulatory updates for a specific framework.
        
        Args:
            framework: Regulatory framework (GDPR, HIPAA, CCPA, SOX)
            year: Optional year to filter (defaults to current year)
            
        Returns:
            List of relevant articles/updates
        """
        if year is None:
            year = datetime.now().year
        
        query = f"{framework} compliance updates {year} latest amendments requirements"
        
        try:
            results = self.search(query, num_results=10, search_type='news')
            
            # Extract relevant information
            updates = []
            for item in results.get('organic', [])[:10]:
                updates.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'date': item.get('date', ''),
                    'source': item.get('source', ''),
                    'framework': framework
                })
            
            # Also check news results
            for item in results.get('news', [])[:5]:
                updates.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'date': item.get('date', ''),
                    'source': item.get('source', ''),
                    'framework': framework,
                    'is_news': True
                })
            
            self.logger.info(f"Found {len(updates)} regulatory updates for {framework}")
            return updates
            
        except SerperError as e:
            self.logger.error(f"Failed to search regulatory updates: {e}")
            return []
    
    def search_compliance_case_studies(
        self,
        framework: str,
        industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for compliance case studies.
        
        Args:
            framework: Regulatory framework
            industry: Optional industry filter
            
        Returns:
            List of case studies
        """
        industry_str = f"{industry} " if industry else ""
        query = f"{framework} {industry_str}compliance case study examples implementation"
        
        try:
            results = self.search(query, num_results=10)
            
            case_studies = []
            for item in results.get('organic', [])[:10]:
                case_studies.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'framework': framework,
                    'industry': industry
                })
            
            self.logger.info(f"Found {len(case_studies)} case studies for {framework}")
            return case_studies
            
        except SerperError as e:
            self.logger.error(f"Failed to search case studies: {e}")
            return []
    
    def search_regulatory_definition(
        self,
        term: str,
        framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for definition of a regulatory term.
        
        Args:
            term: Term to define
            framework: Optional framework context
            
        Returns:
            Definition information
        """
        framework_str = f"{framework} " if framework else ""
        query = f"{framework_str}{term} definition legal compliance meaning"
        
        try:
            results = self.search(query, num_results=5)
            
            # Try to find knowledge graph or answer box
            definition = {
                'term': term,
                'framework': framework,
                'definition': '',
                'sources': []
            }
            
            # Check for knowledge graph
            if 'knowledgeGraph' in results:
                kg = results['knowledgeGraph']
                definition['definition'] = kg.get('description', '')
            
            # Check answer box
            if 'answerBox' in results:
                answer = results['answerBox']
                if not definition['definition']:
                    definition['definition'] = answer.get('snippet', '') or answer.get('answer', '')
            
            # Add top sources
            for item in results.get('organic', [])[:3]:
                definition['sources'].append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', '')
                })
            
            return definition
            
        except SerperError as e:
            self.logger.error(f"Failed to search definition: {e}")
            return {'term': term, 'framework': framework, 'definition': '', 'sources': []}
    
    def verify_requirement(
        self,
        requirement: str,
        framework: str
    ) -> Dict[str, Any]:
        """
        Verify if a requirement is current and accurate.
        
        Args:
            requirement: Requirement text to verify
            framework: Framework to check against
            
        Returns:
            Verification results
        """
        # Create focused query
        query = f"{framework} requirement \"{requirement}\" official documentation"
        
        try:
            results = self.search(query, num_results=5)
            
            verification = {
                'requirement': requirement,
                'framework': framework,
                'verified': False,
                'confidence': 0.0,
                'sources': [],
                'notes': []
            }
            
            # Look for official sources
            official_domains = [
                'europa.eu',  # GDPR
                'hhs.gov',    # HIPAA
                'oag.ca.gov', # CCPA
                'sec.gov',    # SOX
                '.gov',
                'official'
            ]
            
            for item in results.get('organic', [])[:5]:
                link = item.get('link', '').lower()
                source = {
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'is_official': any(domain in link for domain in official_domains)
                }
                verification['sources'].append(source)
                
                if source['is_official']:
                    verification['verified'] = True
                    verification['confidence'] = min(verification['confidence'] + 0.3, 1.0)
            
            if verification['verified']:
                verification['notes'].append("Requirement found in official sources")
            else:
                verification['notes'].append("Could not verify from official sources")
            
            return verification
            
        except SerperError as e:
            self.logger.error(f"Failed to verify requirement: {e}")
            return {
                'requirement': requirement,
                'framework': framework,
                'verified': False,
                'confidence': 0.0,
                'sources': [],
                'notes': ['Verification failed due to API error']
            }
    
    def get_regulatory_news(
        self,
        frameworks: List[str],
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get recent regulatory news for multiple frameworks.
        
        Args:
            frameworks: List of frameworks to check
            days: Number of days to look back
            
        Returns:
            List of news articles
        """
        all_news = []
        
        for framework in frameworks:
            query = f"{framework} compliance news regulations updates"
            
            try:
                results = self.search(query, num_results=5, search_type='news')
                
                for item in results.get('news', []):
                    all_news.append({
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'link': item.get('link', ''),
                        'date': item.get('date', ''),
                        'source': item.get('source', ''),
                        'framework': framework
                    })
                
            except SerperError as e:
                self.logger.error(f"Failed to get news for {framework}: {e}")
                continue
        
        # Sort by date (most recent first)
        all_news.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        self.logger.info(f"Found {len(all_news)} regulatory news articles")
        return all_news
    
    def test_connection(self) -> bool:
        """
        Test connection to Serper API.
        
        Returns:
            True if connection successful
        """
        try:
            if not self.api_key:
                return False
            
            # Simple test query
            results = self.search("test", num_results=1)
            return 'organic' in results or 'searchParameters' in results
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
