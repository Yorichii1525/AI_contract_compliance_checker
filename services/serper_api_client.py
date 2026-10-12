"""
Serper API integration for web search and regulatory monitoring.
Serper provides Google Search API for real-time web scraping.
"""
import os
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time


logger = logging.getLogger(__name__)


class SerperAPIClient:
    """Client for Serper.dev API - Google Search API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Serper API client.
        
        Args:
            api_key: Serper API key. If not provided, reads from SERPER_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('SERPER_API_KEY')
        if not self.api_key:
            logger.warning("No Serper API key provided. Set SERPER_API_KEY environment variable.")
        
        self.base_url = "https://google.serper.dev"
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        self.rate_limit_delay = 1.0  # seconds between requests
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = 'search',  # 'search', 'news', 'images'
        time_range: Optional[str] = None,  # 'd' (day), 'w' (week), 'm' (month), 'y' (year)
        location: str = 'us',
        gl: str = 'us',
        hl: str = 'en'
    ) -> Dict[str, Any]:
        """
        Perform a Google search via Serper API.
        
        Args:
            query: Search query
            num_results: Number of results to return (max 100)
            search_type: Type of search ('search', 'news', 'images')
            time_range: Time range filter
            location: Location for search
            gl: Country code
            hl: Language code
        
        Returns:
            Dictionary containing search results
        """
        if not self.api_key:
            logger.error("Serper API key not configured")
            return {'error': 'API key not configured'}
        
        self._rate_limit()
        
        endpoint = f"{self.base_url}/{search_type}"
        
        payload = {
            'q': query,
            'num': num_results,
            'gl': gl,
            'hl': hl,
            'location': location
        }
        
        if time_range:
            payload['tbs'] = f'qdr:{time_range}'
        
        try:
            logger.info(f"Serper API search: {query}")
            response = requests.post(
                endpoint,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Serper API returned {len(data.get('organic', []))} results")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper API request failed: {e}")
            return {'error': str(e)}
    
    def search_news(
        self,
        query: str,
        num_results: int = 10,
        time_range: Optional[str] = 'w'  # Default to past week
    ) -> List[Dict[str, Any]]:
        """
        Search for news articles.
        
        Args:
            query: Search query
            num_results: Number of results
            time_range: Time filter ('d', 'w', 'm', 'y')
        
        Returns:
            List of news articles
        """
        result = self.search(
            query=query,
            num_results=num_results,
            search_type='news',
            time_range=time_range
        )
        
        if 'error' in result:
            return []
        
        news_items = result.get('news', [])
        return [
            {
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'date': item.get('date', ''),
                'source': item.get('source', ''),
                'imageUrl': item.get('imageUrl', '')
            }
            for item in news_items
        ]
    
    def search_regulatory_updates(
        self,
        framework: str,
        keywords: List[str],
        num_results: int = 20,
        time_range: str = 'w'
    ) -> List[Dict[str, Any]]:
        """
        Search for regulatory updates for a specific framework.
        
        Args:
            framework: Regulatory framework (GDPR, HIPAA, CCPA, SOX)
            keywords: Additional keywords to include
            num_results: Number of results to return
            time_range: Time range ('d', 'w', 'm', 'y')
        
        Returns:
            List of relevant search results
        """
        # Build comprehensive query
        query_parts = [framework]
        query_parts.extend(keywords)
        query_parts.append("update OR amendment OR regulation OR compliance")
        
        query = " ".join(query_parts)
        
        logger.info(f"Searching regulatory updates for {framework}: {query}")
        
        # Search both regular and news
        regular_results = self.search(
            query=query,
            num_results=num_results,
            time_range=time_range
        )
        
        news_results = self.search_news(
            query=query,
            num_results=num_results,
            time_range=time_range
        )
        
        # Combine and deduplicate results
        all_results = []
        
        # Process regular search results
        for item in regular_results.get('organic', []):
            all_results.append({
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'date': item.get('date', ''),
                'source': item.get('source', ''),
                'type': 'search',
                'position': item.get('position', 0)
            })
        
        # Add news results
        for item in news_results:
            # Check if already exists
            if not any(r['link'] == item['link'] for r in all_results):
                all_results.append({
                    **item,
                    'type': 'news',
                    'position': 0
                })
        
        logger.info(f"Found {len(all_results)} total results for {framework}")
        return all_results
    
    def search_official_sources(
        self,
        framework: str,
        official_domains: List[str],
        time_range: str = 'w'
    ) -> List[Dict[str, Any]]:
        """
        Search specific official government/regulatory websites.
        
        Args:
            framework: Regulatory framework
            official_domains: List of official domains to search
            time_range: Time range filter
        
        Returns:
            List of results from official sources
        """
        all_results = []
        
        for domain in official_domains:
            # Build site-specific query
            query = f"site:{domain} {framework} update OR amendment OR guidance"
            
            results = self.search(
                query=query,
                num_results=10,
                time_range=time_range
            )
            
            for item in results.get('organic', []):
                all_results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'date': item.get('date', ''),
                    'source': domain,
                    'type': 'official',
                    'framework': framework
                })
        
        logger.info(f"Found {len(all_results)} results from official sources")
        return all_results
    
    def get_page_content(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL (basic scraping).
        
        Note: For production, use a proper web scraping library like BeautifulSoup.
        
        Args:
            url: URL to fetch
        
        Returns:
            Page content as string, or None if failed
        """
        try:
            self._rate_limit()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None


# Official regulatory sources for each framework
OFFICIAL_SOURCES = {
    'GDPR': [
        'ec.europa.eu',
        'edpb.europa.eu',
        'eur-lex.europa.eu'
    ],
    'HIPAA': [
        'hhs.gov',
        'ocr.hhs.gov',
        'federalregister.gov'
    ],
    'CCPA': [
        'oag.ca.gov',
        'cppa.ca.gov'
    ],
    'SOX': [
        'sec.gov',
        'pcaob.org'
    ]
}


# Default search keywords for each framework
DEFAULT_KEYWORDS = {
    'GDPR': ['data protection', 'privacy', 'EDPB', 'Article 5', 'DPO'],
    'HIPAA': ['health information', 'PHI', 'covered entity', 'business associate'],
    'CCPA': ['consumer privacy', 'personal information', 'data sale', 'opt-out'],
    'SOX': ['financial reporting', 'internal controls', 'audit', 'Section 404']
}
