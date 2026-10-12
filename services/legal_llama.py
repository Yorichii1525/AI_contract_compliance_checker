"""
LegalLLaMA service for generating recommendations and compliant clause text.
Implements LLaMA model integration with GPU detection and caching.
"""
from typing import Optional, Dict, Any
import time

from config.settings import config
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import torch and transformers, make them optional
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except (ImportError, AttributeError) as e:
    logger.warning(f"torch/transformers not available for LegalLLaMA: {e}")
    TRANSFORMERS_AVAILABLE = False
    torch = None
    AutoModelForCausalLM = None
    AutoTokenizer = None


class LegalLLaMA:
    """
    LLaMA model wrapper for legal reasoning and text generation.
    Supports GPU acceleration with automatic CPU fallback.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        use_gpu: Optional[bool] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        """
        Initialize LegalLLaMA model.
        
        Args:
            model_name: HuggingFace model name (default from config)
            use_gpu: Whether to use GPU if available (default from config)
            max_tokens: Maximum tokens to generate (default from config)
            temperature: Sampling temperature (default from config)
        """
        logger.info("Initializing LegalLLaMA model...")
        
        # Configuration
        self.model_name = model_name or config.models.llama_model
        self.use_gpu = use_gpu if use_gpu is not None else config.models.use_gpu
        self.max_tokens = max_tokens or config.llm.max_tokens
        self.temperature = temperature or config.llm.temperature
        self.top_p = config.llm.top_p
        
        # Check if transformers available
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("LegalLLaMA running in fallback mode - transformers not available")
            self.device = "cpu"
            self.model = None
            self.tokenizer = None
            logger.info("LegalLLaMA initialized in fallback mode")
            return
        
        # Detect device
        self.device = self._detect_device()
        logger.info(f"Using device: {self.device}")
        
        # Initialize model and tokenizer
        self.model = None
        self.tokenizer = None
        self._load_model()
        
        logger.info("LegalLLaMA initialized successfully")
    
    def _detect_device(self) -> str:
        """
        Detect available device (GPU or CPU).
        
        Returns:
            Device string ('cuda' or 'cpu')
        """
        if not TRANSFORMERS_AVAILABLE or torch is None:
            return "cpu"
            
        if self.use_gpu and torch.cuda.is_available():
            logger.info("GPU detected and enabled")
            return "cuda"
        else:
            if self.use_gpu and not torch.cuda.is_available():
                logger.warning("GPU requested but not available, falling back to CPU")
            else:
                logger.info("Using CPU as configured")
            return "cpu"
    
    def _load_model(self):
        """
        Load LLaMA model and tokenizer.
        Implements caching and error handling.
        """
        if not TRANSFORMERS_AVAILABLE or AutoModelForCausalLM is None or AutoTokenizer is None:
            logger.warning("Cannot load model - transformers not available")
            return
            
        try:
            start_time = time.time()
            logger.info(f"Loading model: {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=config.models.cache_dir,
                trust_remote_code=True
            )
            
            # Set padding token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("Tokenizer loaded successfully")
            
            # Load model with appropriate settings
            load_kwargs = {
                'cache_dir': config.models.cache_dir,
                'trust_remote_code': True,
                'torch_dtype': torch.float16 if self.device == "cuda" else torch.float32,
                'low_cpu_mem_usage': True
            }
            
            # Add device map for GPU
            if self.device == "cuda":
                load_kwargs['device_map'] = 'auto'
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **load_kwargs
            )
            
            # Move to device if CPU
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            # Set to evaluation mode
            self.model.eval()
            
            elapsed = time.time() - start_time
            logger.info(f"Model loaded successfully in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to load LLaMA model: {e}", exc_info=True)
            raise RuntimeError(f"Failed to load LLaMA model: {e}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop_sequences: Optional[list] = None
    ) -> str:
        """
        Generate text using LLaMA model.
        
        Args:
            prompt: Input prompt for generation
            max_tokens: Maximum tokens to generate (overrides default)
            temperature: Sampling temperature (overrides default)
            top_p: Nucleus sampling parameter (overrides default)
            stop_sequences: List of sequences to stop generation
            
        Returns:
            Generated text
        """
        if not TRANSFORMERS_AVAILABLE or self.model is None or self.tokenizer is None:
            logger.warning("Model not available, returning fallback text")
            return f"[LLaMA unavailable] Fallback response for prompt: {prompt[:100]}..."
        
        try:
            start_time = time.time()
            
            # Use provided values or defaults
            max_new_tokens = max_tokens or self.max_tokens
            temp = temperature if temperature is not None else self.temperature
            nucleus_p = top_p if top_p is not None else self.top_p
            
            logger.debug(
                f"Generating with max_tokens={max_new_tokens}, "
                f"temperature={temp}, top_p={nucleus_p}"
            )
            
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=config.models.max_length
            ).to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temp,
                    top_p=nucleus_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode output
            generated_text = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )
            
            # Remove the prompt from the output
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            elapsed = time.time() - start_time
            logger.debug(f"Generation completed in {elapsed:.2f}s")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error during text generation: {e}", exc_info=True)
            raise RuntimeError(f"Text generation failed: {e}")
    
    def analyze_compliance(
        self,
        clause_text: str,
        regulatory_context: str
    ) -> Dict[str, Any]:
        """
        Perform detailed compliance analysis using LLaMA.
        
        Args:
            clause_text: Text of the clause to analyze
            regulatory_context: Regulatory requirement context
            
        Returns:
            Dictionary with analysis results
        """
        if not TRANSFORMERS_AVAILABLE or self.model is None:
            logger.warning("LLaMA not available for compliance analysis")
            return {
                'raw_response': '[LLaMA unavailable] Basic analysis',
                'compliant': False,
                'issues': ['Unable to perform detailed analysis - AI model unavailable'],
                'confidence': 0.5
            }
            
        try:
            prompt = self._build_analysis_prompt(clause_text, regulatory_context)
            
            logger.debug("Performing compliance analysis with LLaMA")
            
            response = self.generate(
                prompt,
                max_tokens=256,
                temperature=0.3  # Lower temperature for more focused analysis
            )
            
            # Parse response (simplified - could be enhanced with structured output)
            analysis = {
                'raw_response': response,
                'compliant': 'compliant' in response.lower() and 'non-compliant' not in response.lower(),
                'issues': self._extract_issues(response),
                'confidence': 0.8  # Placeholder - could be extracted from response
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error during compliance analysis: {e}")
            return {
                'raw_response': '',
                'compliant': False,
                'issues': [f"Analysis failed: {str(e)}"],
                'confidence': 0.0
            }
    
    def _build_analysis_prompt(
        self,
        clause_text: str,
        regulatory_context: str
    ) -> str:
        """
        Build prompt for compliance analysis.
        
        Args:
            clause_text: Clause text to analyze
            regulatory_context: Regulatory context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are a legal compliance expert. Analyze the following contract clause against the regulatory requirement.

Regulatory Requirement:
{regulatory_context}

Contract Clause:
{clause_text}

Analysis:
Is this clause compliant with the requirement? Identify any issues or missing elements.

Response:"""
        
        return prompt
    
    def _extract_issues(self, response: str) -> list:
        """
        Extract issues from LLaMA response.
        
        Args:
            response: Generated response text
            
        Returns:
            List of identified issues
        """
        # Simple extraction - look for common issue indicators
        issues = []
        
        keywords = ['missing', 'lacks', 'does not', 'fails to', 'insufficient', 'incomplete']
        
        sentences = response.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                issues.append(sentence.strip())
        
        return issues if issues else ['No specific issues identified']
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'device': self.device,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'model_loaded': self.model is not None
        }
    
    def clear_cache(self):
        """Clear GPU cache if using CUDA."""
        if self.device == "cuda":
            torch.cuda.empty_cache()
            logger.info("GPU cache cleared")
