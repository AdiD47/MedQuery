"""
Configuration validation and management for MedQuery.

Validates environment variables and provides typed configuration access.
"""

import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Application configuration with validation."""
    
    def __init__(self):
        self._validate()
    
    # Required configuration
    @property
    def google_api_key(self) -> str:
        """Google Gemini API key (required)."""
        key = os.getenv("GOOGLE_API_KEY", "")
        if not key:
            logger.warning("GOOGLE_API_KEY not set - LLM features will use fallback")
        return key
    
    @property
    def google_chat_model(self) -> str:
        """Google Gemini model name."""
        return os.getenv("GOOGLE_CHAT_MODEL", "gemini-1.5-pro")
    
    # Optional configuration
    @property
    def tavily_api_key(self) -> Optional[str]:
        """Tavily web search API key (optional)."""
        return os.getenv("TAVILY_API_KEY")
    
    @property
    def nvidia_bioaiq_url(self) -> Optional[str]:
        """NVIDIA BioAI-Q endpoint URL (optional)."""
        return os.getenv("NVIDIA_BIOAIQ_URL")
    
    @property
    def chroma_dir(self) -> Path:
        """ChromaDB persistence directory."""
        path = Path(os.getenv("CHROMA_DIR", "./chroma_db"))
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def reports_dir(self) -> Path:
        """PDF reports output directory."""
        path = Path(os.getenv("REPORTS_DIR", "./reports"))
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def log_level(self) -> str:
        """Logging level."""
        return os.getenv("LOG_LEVEL", "INFO").upper()
    
    @property
    def max_query_length(self) -> int:
        """Maximum query length in characters."""
        return int(os.getenv("MAX_QUERY_LENGTH", "500"))
    
    @property
    def request_timeout(self) -> int:
        """Default request timeout in seconds."""
        return int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    @property
    def enable_caching(self) -> bool:
        """Enable LRU caching for external API calls."""
        return os.getenv("ENABLE_CACHING", "true").lower() == "true"
    
    def _validate(self):
        """Validate critical configuration."""
        warnings = []
        
        if not self.google_api_key:
            warnings.append("GOOGLE_API_KEY not set - LLM summarization will use fallback heuristics")
        
        if not self.tavily_api_key:
            warnings.append("TAVILY_API_KEY not set - web search features limited")
        
        if not self.nvidia_bioaiq_url:
            warnings.append("NVIDIA_BIOAIQ_URL not set - NVIDIA AI-Q features disabled")
        
        if warnings:
            logger.warning("Configuration warnings:\n" + "\n".join(f"  - {w}" for w in warnings))
        else:
            logger.info("All optional features configured")
    
    def __repr__(self) -> str:
        return (
            f"Config("
            f"google_model={self.google_chat_model}, "
            f"tavily={'enabled' if self.tavily_api_key else 'disabled'}, "
            f"nvidia={'enabled' if self.nvidia_bioaiq_url else 'disabled'}, "
            f"chroma_dir={self.chroma_dir}"
            f")"
        )


# Global config instance
config = Config()


if __name__ == "__main__":
    # Test configuration
    logging.basicConfig(level=logging.INFO)
    print(config)
    print(f"\nGoogle API Key set: {bool(config.google_api_key)}")
    print(f"Tavily enabled: {bool(config.tavily_api_key)}")
    print(f"NVIDIA enabled: {bool(config.nvidia_bioaiq_url)}")
    print(f"Chroma directory: {config.chroma_dir}")
