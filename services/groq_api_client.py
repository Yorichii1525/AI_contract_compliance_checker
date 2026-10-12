"""
Groq API integration for fast LLM analysis of regulatory updates.
Groq provides ultra-fast inference for LLaMA and other models.
"""
import os
import requests
import logging
from typing import List, Dict, Any, Optional
import json


logger = logging.getLogger(__name__)


class GroqAPIClient:
    """Client for Groq API - Ultra-fast LLM inference."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq API client.
        
        Args:
            api_key: Groq API key. If not provided, reads from GROQ_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            logger.warning("No Groq API key provided. Set GROQ_API_KEY environment variable.")
        
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Available models on Groq
        self.default_model = "llama-3.3-70b-versatile"  # Fast and accurate
        self.models = [
            "llama-3.3-70b-versatile",
            "llama-3.3-70b-specdec",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to Groq.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (default: llama-3.3-70b-versatile)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
        
        Returns:
            API response dictionary
        """
        if not self.api_key:
            logger.error("Groq API key not configured")
            return {'error': 'API key not configured'}
        
        model = model or self.default_model
        
        payload = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': stream
        }
        
        try:
            logger.info(f"Groq API request: model={model}, messages={len(messages)}")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Groq API response received")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request failed: {e}")
            return {'error': str(e)}
    
    def analyze_regulatory_text(
        self,
        text: str,
        framework: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze regulatory text to extract key information.
        
        Args:
            text: Regulatory text to analyze
            framework: Framework (GDPR, HIPAA, CCPA, SOX)
            context: Additional context
        
        Returns:
            Analysis results
        """
        prompt = f"""You are a legal compliance expert specializing in {framework} regulations.

Analyze the following regulatory text and provide:
1. Summary (2-3 sentences)
2. Update Type (New Regulation, Amendment, Clarification, Enforcement, Guidance, Case Law, Proposed Rule)
3. Severity (Critical, High, Medium, Low)
4. Affected Areas (list of contract clause types affected)
5. Required Actions (list of actions organizations should take)
6. Compliance Deadline (if mentioned)
7. Impact Score (0-1 scale indicating how significant this update is)

{f'Context: {context}' if context else ''}

Regulatory Text:
{text}

Provide your analysis in JSON format with keys: summary, update_type, severity, affected_areas, required_actions, compliance_deadline, impact_score, key_changes."""
        
        messages = [
            {
                'role': 'system',
                'content': f'You are an expert in {framework} regulatory compliance. Provide concise, actionable analysis.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ]
        
        response = self.chat_completion(
            messages=messages,
            temperature=0.3,  # Lower temperature for more focused analysis
            max_tokens=1500
        )
        
        if 'error' in response:
            return {'error': response['error']}
        
        try:
            content = response['choices'][0]['message']['content']
            
            # Try to extract JSON from response
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()
            elif '```' in content:
                json_start = content.find('```') + 3
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()
            
            analysis = json.loads(content)
            return analysis
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse Groq response: {e}")
            # Return raw content if JSON parsing fails
            return {
                'summary': response.get('choices', [{}])[0].get('message', {}).get('content', ''),
                'error': f'Failed to parse JSON: {e}'
            }
    
    def summarize_updates(
        self,
        updates: List[Dict[str, Any]],
        framework: str
    ) -> str:
        """
        Generate an executive summary of multiple updates.
        
        Args:
            updates: List of regulatory updates
            framework: Framework name
        
        Returns:
            Executive summary text
        """
        updates_text = "\n\n".join([
            f"Update {i+1}:\nTitle: {u.get('title', 'N/A')}\nSummary: {u.get('summary', 'N/A')}"
            for i, u in enumerate(updates[:10])  # Limit to 10 updates
        ])
        
        prompt = f"""You are a compliance officer writing an executive summary.

Summarize the following {len(updates)} {framework} regulatory updates for senior management.

Focus on:
- Most critical updates requiring immediate action
- Key trends or patterns
- Overall compliance risk level
- Recommended next steps

Updates:
{updates_text}

Provide a concise executive summary (200-300 words)."""
        
        messages = [
            {
                'role': 'system',
                'content': 'You are a senior compliance officer writing executive summaries.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ]
        
        response = self.chat_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=500
        )
        
        if 'error' in response:
            return f"Error generating summary: {response['error']}"
        
        try:
            summary = response['choices'][0]['message']['content']
            return summary
        except (KeyError, IndexError):
            return "Error: Could not generate summary"
    
    def classify_update_impact(
        self,
        update_title: str,
        update_text: str,
        framework: str,
        current_contract_clauses: List[str]
    ) -> Dict[str, Any]:
        """
        Determine how an update impacts existing contract clauses.
        
        Args:
            update_title: Title of the update
            update_text: Full text of the update
            framework: Regulatory framework
            current_contract_clauses: List of clause types in current contracts
        
        Returns:
            Impact assessment
        """
        clauses_text = ", ".join(current_contract_clauses[:20])  # Limit clause list
        
        prompt = f"""You are analyzing how a {framework} regulatory update affects existing contract clauses.

Update: {update_title}

Current Contract Clause Types: {clauses_text}

Update Details:
{update_text[:1500]}  # Limit text length

Determine:
1. Which clause types are affected (from the list above)
2. Severity of impact for each (Critical/High/Medium/Low)
3. Specific changes needed
4. Estimated effort (hours) to update contracts

Provide response in JSON format with keys: affected_clauses (list of dicts with clause_type, severity, changes_needed, estimated_hours)."""
        
        messages = [
            {'role': 'system', 'content': f'You are a {framework} compliance expert.'},
            {'role': 'user', 'content': prompt}
        ]
        
        response = self.chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=1000
        )
        
        if 'error' in response:
            return {'error': response['error']}
        
        try:
            content = response['choices'][0]['message']['content']
            
            # Extract JSON
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()
            elif '```' in content:
                json_start = content.find('```') + 3
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()
            
            impact = json.loads(content)
            return impact
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse impact analysis: {e}")
            return {'error': f'Failed to parse response: {e}'}
    
    def detect_contradictions(
        self,
        new_regulation: str,
        existing_clauses: List[str]
    ) -> List[Dict[str, str]]:
        """
        Detect if new regulation contradicts existing contract clauses.
        
        Args:
            new_regulation: Text of new regulation
            existing_clauses: List of existing clause texts
        
        Returns:
            List of detected contradictions
        """
        clauses_text = "\n\n".join([
            f"Clause {i+1}: {clause[:200]}"  # Truncate long clauses
            for i, clause in enumerate(existing_clauses[:10])
        ])
        
        prompt = f"""Analyze if this new regulation contradicts any existing contract clauses.

New Regulation:
{new_regulation[:1000]}

Existing Clauses:
{clauses_text}

Identify any contradictions, conflicts, or incompatibilities.

Return JSON array with: [{{"clause_number": int, "contradiction": str, "severity": str, "resolution": str}}]"""
        
        messages = [
            {'role': 'system', 'content': 'You are a legal contract analyst.'},
            {'role': 'user', 'content': prompt}
        ]
        
        response = self.chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=1000
        )
        
        if 'error' in response:
            return []
        
        try:
            content = response['choices'][0]['message']['content']
            
            # Extract JSON
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                content = content[json_start:json_end].strip()
            elif '[' in content:
                json_start = content.find('[')
                json_end = content.rfind(']') + 1
                content = content[json_start:json_end]
            
            contradictions = json.loads(content)
            return contradictions if isinstance(contradictions, list) else []
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse contradictions: {e}")
            return []
