"""
Gmail API service for fetching and processing emails.
Handles OAuth authentication, email retrieval, and hyperlink preservation.
"""

import logging
import os
import re
from typing import List, Dict, Optional
from pathlib import Path
import base64

# Google API imports for Gmail integration
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import LLM service for metadata stripping
import llm_service

# Configure logging for email operations
logger = logging.getLogger(__name__)

# Gmail API scopes - read-only access
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _get_gmail_service():
    """
    Authenticate and return Gmail API service instance.
    Uses OAuth with credentials.json and token.json files.

    Returns:
        Gmail API service object

    Raises:
        FileNotFoundError: If credentials.json is missing
        Exception: If authentication fails
    """
    creds = None
    creds_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")

    # Construct absolute paths using pathlib
    backend_dir = Path(__file__).parent
    creds_path = backend_dir / creds_file
    token_path = backend_dir / token_file

    # Load existing token if available
    if token_path.exists():
        logger.info(f"Loading existing token from {token_path}")
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # If no valid credentials, prompt for login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token")
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                logger.error(f"Credentials file not found: {creds_path}")
                raise FileNotFoundError(
                    f"Gmail credentials file not found: {creds_path}. "
                    "Download from Google Cloud Console."
                )

            logger.info("Starting OAuth flow - user login required")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        logger.info(f"Token saved to {token_path}")

    # Build and return Gmail service using googleapiclient
    service = build("gmail", "v1", credentials=creds)
    logger.info("Gmail service authenticated successfully")

    return service


def fetch_emails(
    sender_email: str,
    max_results: int = 50,
    task_id: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Fetch email THREADS from specific sender with hyperlinks preserved.
    Each thread may contain multiple messages - all are combined.

    Args:
        sender_email: Email address to filter by (e.g., "admin@f5bot.com")
        max_results: Maximum number of THREADS to fetch
        task_id: Optional task ID for logging

    Returns:
        List of thread dictionaries with 'id', 'subject', 'body', 'date', 'message_count' keys
        Each thread's body contains all messages combined

    Raises:
        Exception: If Gmail API call fails
    """
    log_prefix = f"[{task_id}]" if task_id else ""

    logger.info(f"{log_prefix} Fetching email THREADS from={sender_email}, limit={max_results}")

    try:
        service = _get_gmail_service()

        # Query THREADS from sender using Gmail search syntax
        query = f"from:{sender_email}"
        results = service.users().threads().list(
            userId="me",
            q=query,
            maxResults=max_results
        ).execute()

        threads = results.get("threads", [])

        if not threads:
            logger.warning(f"{log_prefix} No threads found from {sender_email}")
            return []

        logger.info(f"{log_prefix} Found {len(threads)} threads, fetching details...")

        thread_data_list = []
        for i, thread in enumerate(threads, 1):
            try:
                # Fetch full thread details with all messages using Gmail API
                thread_detail = service.users().threads().get(
                    userId="me",
                    id=thread["id"],
                    format="full"
                ).execute()

                thread_data = _parse_thread(thread_detail)
                thread_data_list.append(thread_data)

                if i % 10 == 0:
                    logger.info(f"{log_prefix} Fetched {i}/{len(threads)} threads")

            except HttpError as e:
                logger.error(f"{log_prefix} Failed to fetch thread {thread['id']}: {e}")
                continue

        logger.info(f"{log_prefix} Successfully fetched {len(thread_data_list)} threads")
        return thread_data_list

    except Exception as e:
        logger.error(f"{log_prefix} Gmail API error: {str(e)}")
        raise Exception(f"Failed to fetch email threads: {str(e)}")


def _parse_thread(thread: Dict) -> Dict[str, str]:
    """
    Parse Gmail thread and combine all messages within it.
    Preserves hyperlinks and conversation flow.

    Args:
        thread: Gmail API thread object containing multiple messages

    Returns:
        Dictionary with id, subject, body, date, message_count fields
        Body contains all messages in thread combined
    """
    messages = thread.get("messages", [])

    if not messages:
        return {
            "id": thread["id"],
            "subject": "No Subject",
            "body": "",
            "date": "Unknown Date",
            "message_count": 0
        }

    # Get thread subject and date from first message
    first_message = messages[0]
    first_headers = first_message["payload"]["headers"]
    thread_subject = next((h["value"] for h in first_headers if h["name"] == "Subject"), "No Subject")
    thread_date = next((h["value"] for h in first_headers if h["name"] == "Date"), "Unknown Date")

    # Combine all messages in thread
    combined_bodies = []
    for i, message in enumerate(messages, 1):
        msg_headers = message["payload"]["headers"]
        msg_date = next((h["value"] for h in msg_headers if h["name"] == "Date"), "Unknown")
        msg_body = _extract_body_with_links(message["payload"])

        # Add message separator with metadata
        combined_bodies.append(f"--- Message {i} of {len(messages)} (Date: {msg_date}) ---")
        combined_bodies.append(msg_body)
        combined_bodies.append("")  # Empty line between messages

    combined_body = "\n".join(combined_bodies)

    logger.debug(f"Parsed thread {thread['id']}: {len(messages)} messages, {len(combined_body)} chars")

    return {
        "id": thread["id"],
        "subject": thread_subject,
        "body": combined_body,
        "date": thread_date,
        "message_count": len(messages)
    }


def _parse_message(message: Dict) -> Dict[str, str]:
    """
    Parse Gmail message and extract relevant fields.
    Preserves hyperlinks in email body.

    Args:
        message: Gmail API message object

    Returns:
        Dictionary with id, subject, body, date fields
    """
    headers = message["payload"]["headers"]

    # Extract subject and date from headers
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")

    # Extract body with hyperlinks preserved
    body = _extract_body_with_links(message["payload"])

    return {
        "id": message["id"],
        "subject": subject,
        "body": body,
        "date": date,
    }


def _extract_body_with_links(payload: Dict) -> str:
    """
    Extract email body and preserve hyperlinks.
    Handles both plain text and HTML parts.

    Args:
        payload: Gmail message payload

    Returns:
        Email body text with hyperlinks preserved
    """
    body = ""

    # Check for body data in payload
    if "body" in payload and "data" in payload["body"]:
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

    # Check for multipart message (parts array)
    elif "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")

            # Prefer HTML for hyperlink preservation
            if mime_type == "text/html" and "data" in part["body"]:
                html_body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                body = _html_to_text_with_links(html_body)
                break

            # Fallback to plain text
            elif mime_type == "text/plain" and "data" in part["body"]:
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

    return body.strip()


def _html_to_text_with_links(html: str) -> str:
    """
    Convert HTML to plain text while preserving hyperlinks.
    Extracts <a> tags and formats as "text (url)".

    Args:
        html: HTML content string

    Returns:
        Plain text with URLs preserved
    """
    # Extract links using regex: <a href="url">text</a>
    link_pattern = re.compile(r'<a[^>]+href=["\'](.*?)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)

    # Replace links with "text (url)" format
    def replace_link(match):
        url = match.group(1)
        text = re.sub(r'<.*?>', '', match.group(2)).strip()  # Strip HTML tags from link text
        return f"{text} ({url})" if text else url

    text = link_pattern.sub(replace_link, html)

    # Remove remaining HTML tags using regex
    text = re.sub(r'<.*?>', '', text)

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)

    return text.strip()


def strip_metadata_with_llm(email_text: str, task_id: Optional[str] = None) -> str:
    """
    Strip email metadata using LLM.
    Removes signatures, headers, timestamps, and other non-content elements.

    Args:
        email_text: Combined email text to clean
        task_id: Optional task ID for logging

    Returns:
        Cleaned email text with only message bodies
    """
    log_prefix = f"[{task_id}]" if task_id else ""

    logger.info(f"{log_prefix} Stripping metadata using LLM ({len(email_text)} chars)")

    # System prompt for metadata stripping
    system_prompt = """You are an email cleaning assistant. Your job is to remove email metadata and keep only the actual message content.

Remove the following:
- Email signatures (e.g., "Sent from my iPhone", "Best regards, John Doe")
- Email headers and technical metadata
- Timestamps and date stamps (unless part of message content)
- Threading artifacts and reply indicators
- Automatic footers and disclaimers
- Unsubscribe links and promotional text

Keep the following:
- Actual message content and conversation
- Hyperlinks that are part of the message
- Questions, answers, and discussion points
- Technical details and code snippets

Return ONLY the cleaned message content. If multiple messages, separate them with "---" ."""

    user_prompt = f"Clean the following email content:\n\n{email_text}"

    try:
        # Call LLM to strip metadata
        cleaned_text = llm_service.analyze_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_id=task_id
        )

        logger.info(f"{log_prefix} Metadata stripped: {len(email_text)} → {len(cleaned_text)} chars")

        return cleaned_text

    except Exception as e:
        logger.error(f"{log_prefix} Metadata stripping failed: {str(e)}")
        # Return original text if stripping fails
        logger.warning(f"{log_prefix} Using original text (metadata stripping failed)")
        return email_text


def combine_emails(emails: List[Dict[str, str]]) -> str:
    """
    Combine multiple emails/threads into single text block for LLM analysis.
    Preserves structure and hyperlinks.

    Args:
        emails: List of email/thread dictionaries

    Returns:
        Combined email text with separators
    """
    combined = []

    for i, email in enumerate(emails, 1):
        combined.append(f"=== EMAIL/THREAD {i} ===")
        combined.append(f"Subject: {email['subject']}")
        combined.append(f"Date: {email['date']}")

        # Include message count if present (from threads)
        if "message_count" in email:
            combined.append(f"Messages in thread: {email['message_count']}")

        combined.append(f"\n{email['body']}\n")

    result = "\n".join(combined)

    logger.info(f"Combined {len(emails)} emails/threads into {len(result)} chars")

    return result
