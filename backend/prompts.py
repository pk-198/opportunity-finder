"""
Prompt loader from YAML configuration.
Provides functions to retrieve LLM prompts for specific sender types.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Cache loaded prompts
_prompts_cache: Optional[Dict] = None


def load_prompts() -> Dict:
    """
    Load prompts from config/prompts.yaml file.
    Uses caching to avoid repeated file reads.

    Returns:
        Dictionary of prompts keyed by sender type

    Raises:
        FileNotFoundError: If prompts.yaml doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    global _prompts_cache

    # Return cached prompts if available
    if _prompts_cache is not None:
        return _prompts_cache

    # Construct path to prompts.yaml using pathlib
    config_dir = Path(__file__).parent / "config"
    prompts_file = config_dir / "prompts.yaml"

    if not prompts_file.exists():
        logger.error(f"Prompts file not found: {prompts_file}")
        raise FileNotFoundError(f"Prompts file not found: {prompts_file}")

    # Load and parse YAML
    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            _prompts_cache = yaml.safe_load(f)
        logger.info(f"Loaded prompts from {prompts_file}")
        return _prompts_cache

    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML: {e}")
        raise


def get_prompt(prompt_key: str) -> Dict[str, str]:
    """
    Get prompt for a specific sender type.

    Args:
        prompt_key: Prompt identifier (e.g., "f5bot_reddit", "haro_opportunities")

    Returns:
        Dictionary with "system_prompt" and "user_prompt" keys

    Raises:
        KeyError: If prompt_key not found in configuration
    """
    prompts = load_prompts()

    if prompt_key not in prompts:
        logger.error(f"Prompt key not found: {prompt_key}")
        available_keys = ", ".join(prompts.keys())
        raise KeyError(f"Prompt key '{prompt_key}' not found. Available: {available_keys}")

    prompt_data = prompts[prompt_key]

    logger.info(f"Retrieved prompt: {prompt_key}")

    return {
        "system_prompt": prompt_data.get("system_prompt", ""),
        "user_prompt": prompt_data.get("user_prompt", ""),
    }


def format_user_prompt(prompt_key: str, email_content: str) -> str:
    """
    Get user prompt with email content injected.

    Args:
        prompt_key: Prompt identifier
        email_content: Email content to inject into {email_content} placeholder

    Returns:
        Formatted user prompt string
    """
    prompt_data = get_prompt(prompt_key)
    user_prompt_template = prompt_data["user_prompt"]

    # Replace {email_content} placeholder with actual content
    formatted_prompt = user_prompt_template.replace("{email_content}", email_content)

    logger.info(f"Formatted user prompt for {prompt_key} ({len(email_content)} chars)")

    return formatted_prompt


def reload_prompts() -> None:
    """
    Clear cached prompts to force reload from file.
    Useful for development/testing when prompts change.
    """
    global _prompts_cache
    _prompts_cache = None
    logger.info("Prompts cache cleared - will reload on next request")
