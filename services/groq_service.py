"""Groq API Service - Fast LLM inference for compliance recommendations."""

import logging
import os
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)


class GroqError(Exception):
    """Base exception for Groq API errors."""
    pass


class GroqService:
    """Service for generating compliance recommendations using Groq API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq service.
        
        Args:
            api_key: Groq API key (or set GROQ_API_KEY env variable)
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        
        if not self.api_key:
            self.logger.warning(
                "Groq API key not found. Set GROQ_API_KEY environment variable. "
                "Get your key from https://console.groq.com"
            )
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Groq client."""
        if not self.api_key:
            return
        
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.logger.info("Groq client initialized successfully")
        except ImportError:
            self.logger.error("Groq library not installed. Install with: pip install groq")
        except Exception as e:
            self.logger.error(f"Failed to initialize Groq client: {e}")
    
    def generate_compliant_clause(
        self,
        clause_type: str,
        framework: str,
        context: Optional[str] = None,
        current_clause: Optional[str] = None,
        issues: Optional[List[str]] = None,
        model: str = "llama-3.3-70b-versatile"
    ) -> Dict[str, Any]:
        """
        Generate a compliant clause using Groq.
        
        Args:
            clause_type: Type of clause (e.g., 'Data Processing', 'Security')
            framework: Regulatory framework (GDPR, HIPAA, etc.)
            context: Additional context about the contract
            current_clause: Current clause text (if updating)
            issues: List of compliance issues to address
            model: Groq model to use
            
        Returns:
            Generated clause with explanation
        """
        if not self.client:
            raise GroqError("Groq client not initialized. Check API key.")
        
        try:
            # Build prompt
            prompt = self._build_clause_generation_prompt(
                clause_type, framework, context, current_clause, issues
            )
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal compliance expert specializing in generating compliant contract clauses. Provide clear, legally sound clauses that meet regulatory requirements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Extract response
            generated_text = response.choices[0].message.content
            
            # Parse response (expecting JSON format)
            try:
                result = json.loads(generated_text)
            except json.JSONDecodeError:
                # If not JSON, structure it ourselves
                result = {
                    'clause': generated_text,
                    'explanation': 'Generated compliant clause',
                    'key_points': []
                }
            
            result['model'] = model
            result['clause_type'] = clause_type
            result['framework'] = framework
            
            self.logger.info(f"Generated compliant clause for {clause_type} under {framework}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate clause: {e}")
            raise GroqError(f"Clause generation failed: {e}")
    
    def analyze_compliance_risk(
        self,
        clause_text: str,
        framework: str,
        model: str = "llama-3.3-70b-versatile"
    ) -> Dict[str, Any]:
        """
        Analyze compliance risk of a clause.
        
        Args:
            clause_text: Text of the clause
            framework: Regulatory framework
            model: Groq model to use
            
        Returns:
            Risk analysis
        """
        if not self.client:
            raise GroqError("Groq client not initialized. Check API key.")
        
        try:
            prompt = f"""Analyze the following contract clause for compliance with {framework}:

CLAUSE:
{clause_text}

Provide a JSON response with:
{{
    "risk_level": "low/medium/high",
    "risk_score": 0-100,
    "issues": ["list of specific compliance issues"],
    "recommendations": ["list of specific recommendations"],
    "compliant": true/false,
    "explanation": "brief explanation"
}}"""
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a legal compliance expert specializing in {framework}. Analyze clauses for compliance risks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback parsing
                analysis = {
                    'risk_level': 'medium',
                    'risk_score': 50,
                    'issues': ['Analysis failed to parse'],
                    'recommendations': ['Manual review recommended'],
                    'compliant': False,
                    'explanation': analysis_text
                }
            
            analysis['framework'] = framework
            analysis['model'] = model
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze compliance risk: {e}")
            raise GroqError(f"Risk analysis failed: {e}")
    
    def generate_compliance_summary(
        self,
        report_data: Dict[str, Any],
        frameworks: List[str],
        model: str = "llama-3.3-70b-versatile"
    ) -> str:
        """
        Generate an executive summary of compliance analysis.
        
        Args:
            report_data: Complete compliance report data
            frameworks: List of frameworks analyzed
            model: Groq model to use
            
        Returns:
            Executive summary text
        """
        if not self.client:
            raise GroqError("Groq client not initialized. Check API key.")
        
        try:
            prompt = f"""Generate an executive summary for this compliance analysis:

Frameworks Analyzed: {', '.join(frameworks)}
Overall Score: {report_data.get('overall_score', 0):.1f}%
Total Clauses: {report_data.get('total_clauses', 0)}
Compliant: {report_data.get('compliant_count', 0)}
Non-Compliant: {report_data.get('non_compliant_count', 0)}
High Risk: {report_data.get('high_risk_count', 0)}

Framework Scores:
{json.dumps(report_data.get('framework_scores', {}), indent=2)}

Create a professional 3-paragraph executive summary covering:
1. Overall compliance status and key metrics
2. Critical risks and areas requiring immediate attention
3. Recommended next steps and priorities"""
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a compliance officer creating executive summaries for leadership. Be clear, concise, and actionable."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content
            
            self.logger.info("Generated compliance summary")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            raise GroqError(f"Summary generation failed: {e}")
    
    def compare_frameworks(
        self,
        clause_text: str,
        frameworks: List[str],
        model: str = "llama-3.3-70b-versatile"
    ) -> Dict[str, Any]:
        """
        Compare how a clause complies across multiple frameworks.
        
        Args:
            clause_text: Text of the clause
            frameworks: List of frameworks to compare
            model: Groq model to use
            
        Returns:
            Comparison analysis
        """
        if not self.client:
            raise GroqError("Groq client not initialized. Check API key.")
        
        try:
            prompt = f"""Compare how this clause complies with multiple regulatory frameworks:

CLAUSE:
{clause_text}

FRAMEWORKS: {', '.join(frameworks)}

Provide a JSON response with:
{{
    "comparison": {{
        "framework_name": {{
            "compliant": true/false,
            "score": 0-100,
            "specific_requirements_met": [],
            "gaps": []
        }}
    }},
    "universal_strengths": [],
    "universal_gaps": [],
    "recommendations": []
}}"""
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a multi-framework compliance expert. Compare compliance across different regulations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            comparison_text = response.choices[0].message.content
            
            try:
                comparison = json.loads(comparison_text)
            except json.JSONDecodeError:
                comparison = {
                    'comparison': {},
                    'universal_strengths': [],
                    'universal_gaps': [],
                    'recommendations': ['Parse error - manual review needed'],
                    'raw_response': comparison_text
                }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Failed to compare frameworks: {e}")
            raise GroqError(f"Framework comparison failed: {e}")
    
    def _build_clause_generation_prompt(
        self,
        clause_type: str,
        framework: str,
        context: Optional[str],
        current_clause: Optional[str],
        issues: Optional[List[str]]
    ) -> str:
        """Build prompt for clause generation."""
        prompt_parts = [
            f"Generate a compliant {clause_type} clause for {framework}."
        ]
        
        if context:
            prompt_parts.append(f"\nCONTEXT:\n{context}")
        
        if current_clause:
            prompt_parts.append(f"\nCURRENT CLAUSE:\n{current_clause}")
        
        if issues:
            prompt_parts.append(f"\nISSUES TO ADDRESS:\n" + "\n".join(f"- {issue}" for issue in issues))
        
        prompt_parts.append("""
Provide a JSON response with:
{
    "clause": "the generated compliant clause text",
    "explanation": "why this clause is compliant",
    "key_points": ["list of key compliance points addressed"],
    "legal_references": ["relevant legal articles or sections"]
}""")
        
        return "\n".join(prompt_parts)
    
    def test_connection(self) -> bool:
        """
        Test connection to Groq API.
        
        Returns:
            True if connection successful
        """
        try:
            if not self.client:
                return False
            
            # Simple test request with updated model
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": "Say 'OK' if you can read this."}
                ],
                max_tokens=10
            )
            
            return len(response.choices) > 0
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
