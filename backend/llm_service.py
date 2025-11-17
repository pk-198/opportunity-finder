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

    logger.info(f"{log_prefix} LLM call - provider={provider}, model={model}")
    logger.debug(f"{log_prefix} LLM timeout: {LLM_TIMEOUT}s")
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

        logger.info(f"{log_prefix} LLM call completed successfully")
        logger.debug(f"{log_prefix} Response length: {len(result)} chars")
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
    import re
    import json

    log_prefix = f"[{task_id}]" if task_id else ""

    logger.info(f"{log_prefix} Parsing markdown to JSON")
    logger.debug(f"{log_prefix} Input length: {len(markdown_text)} chars")

    # Get parsing model config (defaults to GROQ fast model)
    parsing_model = os.getenv("GROQ_PARSING_MODEL", "llama-3.1-8b-instant")
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        logger.warning(f"{log_prefix} GROQ_API_KEY not set, skipping parsing - returning raw markdown")
        return markdown_text

    system_prompt = """You are a markdown to JSON converter. Convert the provided markdown analysis into a clean, structured JSON format.

CRITICAL RULES:
1. Output ONLY valid JSON - no explanations, no markdown code blocks, no extra text
2. Do NOT wrap the JSON in ```json``` or any markdown formatting
3. Start your response directly with { and end with }
4. Preserve ALL information from the markdown
5. Keep ALL hyperlinks exactly as they appear
6. Maintain hierarchical structure from markdown
7. Use consistent key names across all sections

EXAMPLE OUTPUT FORMAT (adapt structure to match input):
{"sections":[{"title":"SECTION 1","opportunities":[{"name":"...","link":"...","priority":"High"}]}]}"""

    user_prompt = f"Convert this markdown to structured JSON (output ONLY the JSON, no markdown formatting):\n\n{markdown_text}"

    try:
        # Use GROQ fast model for parsing with JSON mode if supported
        client = Groq(
            api_key=groq_api_key,
            timeout=30  # Shorter timeout for parsing (30 seconds)
        )

        logger.debug(f"{log_prefix} Calling parsing LLM - model={parsing_model}")

        # Try to use JSON mode (not all GROQ models support it)
        try:
            response = client.chat.completions.create(
                model=parsing_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},  # Force JSON output
                timeout=30
            )
            logger.debug(f"{log_prefix} Used JSON mode for parsing")
        except Exception:
            # Fallback if JSON mode not supported
            logger.debug(f"{log_prefix} JSON mode not supported, using regular mode")
            response = client.chat.completions.create(
                model=parsing_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                timeout=30
            )

        result = response.choices[0].message.content

        # Log raw parsing LLM output before post-processing
        logger.debug(f"{log_prefix} Raw parsing LLM output (before extraction): {result[:500]}...")

        # Post-process: Extract JSON from markdown code blocks if present
        result = _extract_json_from_text(result)

        # Log after extraction
        logger.debug(f"{log_prefix} After extraction: {result[:500]}...")

        # Validate that it's valid JSON
        try:
            json.loads(result)  # Validate JSON
            logger.info(f"{log_prefix} Parsing completed successfully - valid JSON")
        except json.JSONDecodeError as e:
            logger.warning(f"{log_prefix} Parsed output is not valid JSON: {e}")
            logger.debug(f"{log_prefix} Invalid JSON output: {result[:200]}...")
            # Return original markdown if JSON is invalid
            return markdown_text

        logger.debug(f"{log_prefix} Output length: {len(result)} chars")
        return result

    except Exception as e:
        logger.error(f"{log_prefix} Parsing failed: {str(e)}")
        # Return original markdown if parsing fails
        logger.warning(f"{log_prefix} Using original markdown (parsing failed)")
        return markdown_text


def _extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text that might contain markdown code blocks or extra text.

    Args:
        text: Text that might contain JSON

    Returns:
        Extracted JSON string
    """
    import re

    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
    json_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    match = re.search(json_block_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try to find JSON object bounds (starts with { ends with })
    # Find the first { and last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace + 1]

    # If no JSON found, return original text
    return text.strip()


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
