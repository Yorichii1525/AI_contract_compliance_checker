"""
Knowledge base loader for JSONL and CSV files.
Loads and indexes legal contract data for regulatory analysis.
"""
import json
import csv
import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass
import re


logger = logging.getLogger(__name__)


@dataclass
class ContractKnowledge:
    """Represents knowledge from a contract in the dataset."""
    contract_id: str
    filename: str
    clause_type: str
    clause_text: str
    keywords: List[str]
    split: str  # train/test
    
    def matches_keywords(self, keywords: List[str]) -> bool:
        """Check if contract matches any of the keywords."""
        text_lower = f"{self.clause_type} {self.clause_text}".lower()
        return any(kw.lower() in text_lower for kw in keywords)


class KnowledgeBaseLoader:
    """Loads and manages knowledge base from JSONL and CSV files."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize knowledge base loader.
        
        Args:
            base_dir: Base directory containing knowledge base files
        """
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.contracts: List[ContractKnowledge] = []
        self.manifest: Dict[str, Dict[str, Any]] = {}
        self.clause_types: Set[str] = set()
        self.frameworks: Dict[str, List[str]] = {
            'GDPR': [],
            'HIPAA': [],
            'CCPA': [],
            'SOX': []
        }
        
        logger.info(f"Initializing KnowledgeBaseLoader with base_dir: {self.base_dir}")
    
    def load_manifest(self, manifest_path: Optional[Path] = None) -> int:
        """
        Load CUAD manifest CSV file.
        
        Args:
            manifest_path: Path to cuad_manifest.csv
        
        Returns:
            Number of contracts loaded
        """
        if manifest_path is None:
            manifest_path = self.base_dir / "cuad_manifest.csv"
        
        if not manifest_path.exists():
            logger.warning(f"Manifest file not found: {manifest_path}")
            return 0
        
        logger.info(f"Loading manifest from: {manifest_path}")
        
        count = 0
        with open(manifest_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                contract_id = row.get('contract_id', '')
                self.manifest[contract_id] = {
                    'filename': row.get('filename', ''),
                    'num_qas': int(row.get('num_qas', 0)),
                    'split': row.get('split', 'train'),
                    'char_count': int(row.get('char_count', 0))
                }
                count += 1
        
        logger.info(f"Loaded {count} contracts from manifest")
        return count
    
    def load_jsonl(
        self,
        jsonl_path: Optional[Path] = None,
        limit: Optional[int] = None
    ) -> int:
        """
        Load CUAD JSONL file with contract Q&A data.
        
        Args:
            jsonl_path: Path to JSONL file (default: cuad_sft_train.jsonl)
            limit: Maximum number of entries to load (for large files)
        
        Returns:
            Number of entries loaded
        """
        if jsonl_path is None:
            jsonl_path = self.base_dir / "cuad_sft_train.jsonl"
        
        if not jsonl_path.exists():
            logger.warning(f"JSONL file not found: {jsonl_path}")
            return 0
        
        logger.info(f"Loading JSONL from: {jsonl_path}")
        
        count = 0
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if limit and count >= limit:
                        break
                    
                    try:
                        entry = json.loads(line.strip())
                        
                        # Extract information
                        instruction = entry.get('instruction', '')
                        input_text = entry.get('input', '')
                        output_text = entry.get('output', '')
                        
                        # Extract clause type from instruction
                        clause_type = self._extract_clause_type(instruction)
                        if clause_type:
                            self.clause_types.add(clause_type)
                        
                        # Create contract knowledge entry
                        contract_id = f"jsonl_{line_num}"
                        knowledge = ContractKnowledge(
                            contract_id=contract_id,
                            filename=f"line_{line_num}",
                            clause_type=clause_type or "Unknown",
                            clause_text=input_text[:500],  # First 500 chars
                            keywords=self._extract_keywords(instruction + input_text),
                            split="train"
                        )
                        
                        self.contracts.append(knowledge)
                        count += 1
                        
                        if count % 1000 == 0:
                            logger.info(f"Loaded {count} entries from JSONL...")
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSONL line {line_num}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error loading JSONL file: {e}")
        
        logger.info(f"Loaded {count} entries from JSONL")
        logger.info(f"Found {len(self.clause_types)} unique clause types")
        return count
    
    def _extract_clause_type(self, text: str) -> Optional[str]:
        """Extract clause type from instruction text."""
        # Common patterns in CUAD dataset
        patterns = [
            r'related to "([^"]+)"',
            r'parts \(if any\) of this contract related to "([^"]+)"',
            r'contract related to "([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_keywords(self, text: str, min_length: int = 4, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text."""
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'with', 'from', 'this',
            'that', 'will', 'have', 'has', 'been', 'their', 'they', 'what',
            'which', 'when', 'where', 'who', 'would', 'should', 'could'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter and count
        word_freq = {}
        for word in words:
            if len(word) >= min_length and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def categorize_by_framework(self):
        """Categorize loaded contracts by regulatory framework."""
        framework_keywords = {
            'GDPR': ['data protection', 'privacy', 'personal data', 'gdpr', 'consent', 'right to erasure'],
            'HIPAA': ['health information', 'hipaa', 'phi', 'medical', 'healthcare', 'patient'],
            'CCPA': ['california', 'ccpa', 'consumer privacy', 'personal information', 'sale of data'],
            'SOX': ['financial', 'audit', 'sox', 'internal controls', 'financial reporting']
        }
        
        for contract in self.contracts:
            for framework, keywords in framework_keywords.items():
                if contract.matches_keywords(keywords):
                    self.frameworks[framework].append(contract.contract_id)
        
        logger.info("Categorized contracts by framework:")
        for framework, contracts in self.frameworks.items():
            logger.info(f"  {framework}: {len(contracts)} contracts")
    
    def search_contracts(
        self,
        keywords: List[str],
        clause_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[ContractKnowledge]:
        """
        Search contracts by keywords and clause types.
        
        Args:
            keywords: Keywords to search for
            clause_types: Filter by clause types
            limit: Maximum results to return
        
        Returns:
            List of matching contracts
        """
        results = []
        
        for contract in self.contracts:
            # Check clause type filter
            if clause_types and contract.clause_type not in clause_types:
                continue
            
            # Check keywords
            if contract.matches_keywords(keywords):
                results.append(contract)
                
                if len(results) >= limit:
                    break
        
        logger.info(f"Found {len(results)} contracts matching search")
        return results
    
    def get_clause_types(self) -> List[str]:
        """Get list of all known clause types."""
        return sorted(list(self.clause_types))
    
    def get_framework_contracts(self, framework: str, limit: Optional[int] = None) -> List[ContractKnowledge]:
        """
        Get contracts relevant to a specific framework.
        
        Args:
            framework: Framework name (GDPR, HIPAA, CCPA, SOX)
            limit: Maximum contracts to return
        
        Returns:
            List of relevant contracts
        """
        contract_ids = self.frameworks.get(framework, [])
        if limit:
            contract_ids = contract_ids[:limit]
        
        contracts = [c for c in self.contracts if c.contract_id in contract_ids]
        logger.info(f"Retrieved {len(contracts)} contracts for {framework}")
        return contracts
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded knowledge base."""
        return {
            'total_contracts': len(self.contracts),
            'manifest_entries': len(self.manifest),
            'unique_clause_types': len(self.clause_types),
            'frameworks': {
                framework: len(contracts)
                for framework, contracts in self.frameworks.items()
            },
            'clause_types': self.get_clause_types()
        }
