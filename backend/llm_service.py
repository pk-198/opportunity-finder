"""
LLM service with switchable providers (OpenAI/GROQ).
Handles LLM API calls with 180-second timeout and detailed logging.
"""

import logging
import os
from typing import Dict, Optional
from openai import OpenAI
from groq import Groq

# Configure logging for LLM operations
logger = logging.getLogger(__name__)

# LLM timeout in seconds from env or default
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "180"))


def _get_provider_config() -> Dict[str, str]:
    """
    Read LLM provider configuration from environment variables.

    Returns:
        Dictionary with provider, api_key, and model

    Raises:
        ValueError: If required environment variables are missing
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")

    else:
        raise ValueError(f"Invalid LLM_PROVIDER: {provider}. Must be 'openai' or 'groq'")

    return {
        "provider": provider,
        "api_key": api_key,
        "model": model,
    }


def analyze_with_llm(
    system_prompt: str,
    user_prompt: str,
    task_id: Optional[str] = None
) -> str:
    """
    Analyze content using configured LLM provider.

    Args:
        system_prompt: System instructions for LLM
        user_prompt: User query/content to analyze
        task_id: Optional task ID for logging

    Returns:
        LLM response text

    Raises:
        Exception: If LLM call fails or times out
    """
    config = _get_provider_config()
    provider = config["provider"]
    model = config["model"]

    log_prefix = f"[{task_id}]" if task_id else ""

    logger.info(f"{log_prefix} LLM call start - provider={provider}, model={model}, timeout={LLM_TIMEOUT}s")
    logger.debug(f"{log_prefix} System prompt length: {len(system_prompt)} chars")
    logger.debug(f"{log_prefix} User prompt length: {len(user_prompt)} chars")

    try:
        if provider == "openai":
            # Initialize OpenAI client with timeout
            client = OpenAI(
                api_key=config["api_key"],
                timeout=LLM_TIMEOUT
            )

            # Make API call with chat completion
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                timeout=LLM_TIMEOUT
            )

            result = response.choices[0].message.content

        elif provider == "groq":
            # Initialize GROQ client with timeout
            client = Groq(
                api_key=config["api_key"],
                timeout=LLM_TIMEOUT
            )

            # Make API call with chat completion
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                timeout=LLM_TIMEOUT
            )

            result = response.choices[0].message.content

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info(f"{log_prefix} LLM call success - response length: {len(result)} chars")
        return result

    except Exception as e:
        logger.error(f"{log_prefix} LLM call failed: {str(e)}")
        raise Exception(f"LLM analysis failed: {str(e)}")


def parse_markdown_to_json(
    markdown_text: str,
    task_id: Optional[str] = None
) -> str:
    """
    Parse markdown analysis output to structured JSON using fast/cheap LLM.
    Uses GROQ llama-3.1-8b-instant for cost-effective parsing.

    Args:
        markdown_text: Markdown formatted analysis from main LLM
        task_id: Optional task ID for logging

    Returns:
        JSON string with structured analysis data

    Raises:
        Exception: If parsing fails
    """
    log_prefix = f"[{task_id}]" if task_id else ""

    logger.info(f"{log_prefix} Parsing markdown to JSON ({len(markdown_text)} chars)")

    # Get parsing model config (defaults to GROQ fast model)
    parsing_model = os.getenv("GROQ_PARSING_MODEL", "llama-3.1-8b-instant")
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        logger.warning(f"{log_prefix} GROQ_API_KEY not set, skipping parsing - returning raw markdown")
        return markdown_text

    system_prompt = """You are a markdown to JSON converter. Convert the provided markdown analysis into a clean, structured JSON format.

Rules:
1. Preserve ALL information from the markdown
2. Extract sections with clear headers
3. For each item/opportunity, create a structured object
4. Maintain hierarchical structure from markdown
5. Keep ALL hyperlinks exactly as they appear
6. Return ONLY valid JSON, no markdown formatting
7. If the input is not well-structured markdown, return it as a single "content" field"""

    user_prompt = f"Convert this markdown to structured JSON:\n\n{markdown_text}"

    try:
        # Use GROQ fast model for parsing
        client = Groq(
            api_key=groq_api_key,
            timeout=30  # Shorter timeout for parsing (30 seconds)
        )

        logger.info(f"{log_prefix} Calling parsing LLM - model={parsing_model}")

        response = client.chat.completions.create(
            model=parsing_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            timeout=30
        )

        result = response.choices[0].message.content

        logger.info(f"{log_prefix} Parsing complete - output length: {len(result)} chars")

        return result

    except Exception as e:
        logger.error(f"{log_prefix} Parsing failed: {str(e)}")
        # Return original markdown if parsing fails
        logger.warning(f"{log_prefix} Using original markdown (parsing failed)")
        return markdown_text


def test_llm_connection() -> Dict[str, str]:
    """
    Test LLM connection with a simple prompt.
    Useful for validating configuration during setup.

    Returns:
        Dictionary with status and message

    Raises:
        Exception: If connection test fails
    """
    try:
        config = _get_provider_config()
        logger.info(f"Testing LLM connection - provider={config['provider']}, model={config['model']}")

        response = analyze_with_llm(
            system_prompt="You are a helpful assistant.",
            user_prompt="Respond with 'OK' if you can read this.",
            task_id="connection-test"
        )

        return {
            "status": "success",
            "provider": config["provider"],
            "model": config["model"],
            "message": f"Connection successful: {response[:100]}"
        }

    except Exception as e:
        logger.error(f"LLM connection test failed: {str(e)}")
        raise
