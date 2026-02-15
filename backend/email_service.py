"""
Gmail API service for fetching and processing emails.
Handles OAuth authentication, email retrieval, and hyperlink preservation.
"""

import logging
import os
import re
import email.utils  # RFC 2822 date parsing for Gmail message dates
from datetime import datetime as dt, timezone
from typing import Any, List, Dict, Optional
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
    logger.debug(f"[AUTH] Checking for existing token at: {token_path}")
    if token_path.exists():
        logger.info(f"[AUTH] ✓ Token file found, loading credentials")
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        logger.info(f"[AUTH] ✓ Credentials loaded from token file")
        logger.debug(f"[AUTH] Credential status - Valid: {creds.valid}, Expired: {creds.expired if hasattr(creds, 'expired') else 'N/A'}")
    else:
        logger.info(f"[AUTH] No existing token found")

    # If no valid credentials, prompt for login
    if not creds or not creds.valid:
        logger.info(f"[AUTH] Credentials need refresh or new login")
        if creds and creds.expired and creds.refresh_token:
            logger.info("[AUTH] Refreshing expired token...")
            try:
                creds.refresh(Request())
                logger.info("[AUTH] ✓ Token refreshed successfully")
            except Exception as e:
                logger.error(f"[AUTH] ✗ Token refresh failed: {e}")
                raise
        else:
            logger.info("[AUTH] New OAuth flow required")
            if not creds_path.exists():
                logger.error(f"[AUTH] ✗ Credentials file not found: {creds_path}")
                raise FileNotFoundError(
                    f"Gmail credentials file not found: {creds_path}. "
                    "Download from Google Cloud Console."
                )

            logger.info("[AUTH] Starting OAuth flow - user login required")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            logger.info("[AUTH] Opening browser for OAuth consent...")
            creds = flow.run_local_server(port=0)
            logger.info("[AUTH] ✓ OAuth flow completed successfully")

        # Save credentials for future use
        logger.info(f"[AUTH] Saving credentials to {token_path}")
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        logger.info(f"[AUTH] ✓ Token saved successfully")

    # Build Gmail service with credentials only
    # The build() function will automatically create a requests-based transport
    # when only credentials are provided (no http parameter)
    logger.info("[AUTH] Building Gmail API service v1...")
    service = build("gmail", "v1", credentials=creds)
    logger.info("[AUTH] ✓ Gmail service built successfully")

    return service


def fetch_emails(
    sender_email: str,
    max_results: int = 50,
    task_id: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Fetch INDIVIDUAL MESSAGES from email threads sent by specific sender.
    **CHANGED**: Now returns individual messages instead of combined threads!

    Args:
        sender_email: Email address to filter by (e.g., "admin@f5bot.com")
        max_results: Maximum number of THREADS to fetch (each thread may contain multiple messages)
        task_id: Optional task ID for logging

    Returns:
        List of INDIVIDUAL MESSAGE dictionaries with keys:
        - message_id: Unique message identifier
        - thread_id: Parent thread identifier
        - message_number: Position in thread (1, 2, 3...)
        - total_in_thread: Total messages in parent thread
        - subject: Email subject
        - from: Sender email address
        - date: Email date
        - body: Message body with hyperlinks preserved

    Raises:
        Exception: If Gmail API call fails
    """
    log_prefix = f"[{task_id}]" if task_id else ""

    logger.info(f"{log_prefix} ========== FETCH EMAILS START ==========")
    logger.info(f"{log_prefix} [FETCH] Target sender: {sender_email}")
    logger.info(f"{log_prefix} [FETCH] Max results: {max_results}")

    try:
        # Step 1: Get authenticated Gmail service
        logger.info(f"{log_prefix} [FETCH] Step 1: Getting authenticated Gmail service")
        service = _get_gmail_service()
        logger.info(f"{log_prefix} [FETCH] ✓ Gmail service obtained")

        # Step 2: Query THREADS from sender using Gmail search syntax
        query = f"from:{sender_email}"
        logger.info(f"{log_prefix} [FETCH] Step 2: Querying Gmail API for threads")
        logger.info(f"{log_prefix} [FETCH] Query: {query}")
        logger.info(f"{log_prefix} [FETCH] Executing threads().list() API call...")

        try:
            # Over-fetch to compensate for Gmail API ordering by matching message date
            # (threads with user replies get ranked by the older sender message, not the latest reply)
            fetch_limit = min(max_results * 3, 100)
            logger.info(f"{log_prefix} [FETCH] Over-fetching {fetch_limit} threads (requested {max_results}) to correct ordering")
            results = service.users().threads().list(
                userId="me",
                q=query,
                maxResults=fetch_limit
            ).execute()
            logger.info(f"{log_prefix} [FETCH] ✓ API call successful")
        except Exception as api_error:
            logger.error(f"{log_prefix} [FETCH] ✗ API call failed: {api_error}")
            logger.error(f"{log_prefix} [FETCH] Error type: {type(api_error).__name__}")
            raise

        threads = results.get("threads", [])
        logger.info(f"{log_prefix} [FETCH] API response received - {len(threads)} threads found")

        if not threads:
            logger.warning(f"{log_prefix} [FETCH] ⚠ No threads found from {sender_email}")
            logger.info(f"{log_prefix} ========== FETCH EMAILS END (No Results) ==========")
            return []

        # Step 3: Fetch full details for each thread and extract INDIVIDUAL MESSAGES
        logger.info(f"{log_prefix} [FETCH] Step 3: Fetching threads and extracting individual messages")
        all_messages = []  # Will contain ALL individual messages from ALL threads
        threads_processed = 0

        for i, thread in enumerate(threads, 1):
            thread_id = thread["id"]
            logger.debug(f"{log_prefix} [FETCH] Processing thread {i}/{len(threads)} - ID: {thread_id[:12]}...")

            try:
                # Fetch full thread details with all messages using Gmail API
                logger.debug(f"{log_prefix} [FETCH]   → Calling threads().get() for thread {i}")
                thread_detail = service.users().threads().get(
                    userId="me",
                    id=thread_id,
                    format="full"
                ).execute()
                logger.debug(f"{log_prefix} [FETCH]   ✓ Thread details fetched")

                # Extract individual messages from thread (NEW: message-level instead of thread-level)
                messages = thread_detail.get("messages", [])
                total_in_thread = len(messages)
                logger.debug(f"{log_prefix} [FETCH]   → Extracting {total_in_thread} individual messages from thread")

                # Get thread subject from first message
                first_headers = messages[0]["payload"]["headers"] if messages else []
                thread_subject = next((h["value"] for h in first_headers if h["name"] == "Subject"), "No Subject")

                # Process each message in the thread individually
                for msg_num, message in enumerate(messages, 1):
                    msg_headers = message["payload"]["headers"]

                    # Extract message metadata
                    msg_from = next((h["value"] for h in msg_headers if h["name"] == "From"), sender_email)
                    msg_date = next((h["value"] for h in msg_headers if h["name"] == "Date"), "Unknown")
                    msg_body = _extract_body_with_links(message["payload"])

                    # Create individual message object with thread metadata
                    message_obj = {
                        "message_id": message["id"],  # Unique message ID
                        "thread_id": thread_id,  # Parent thread ID
                        "message_number": msg_num,  # Position in thread (1, 2, 3...)
                        "total_in_thread": total_in_thread,  # Total messages in thread
                        "subject": thread_subject,  # Thread subject
                        "from": msg_from,  # Sender
                        "date": msg_date,  # Message date
                        "body": msg_body  # Message body with hyperlinks
                    }

                    all_messages.append(message_obj)

                threads_processed += 1
                logger.debug(f"{log_prefix} [FETCH]   ✓ Extracted {total_in_thread} messages from thread {i}")

                # Progress logging every 5 threads
                if i % 5 == 0:
                    logger.info(f"{log_prefix} [FETCH] Progress: {i}/{len(threads)} threads processed ({len(all_messages)} total messages)")

            except HttpError as e:
                logger.error(f"{log_prefix} [FETCH]   ✗ Failed to fetch thread {thread_id}: {e}")
                logger.error(f"{log_prefix} [FETCH]   Error code: {e.resp.status if hasattr(e, 'resp') else 'unknown'}")
                continue
            except Exception as e:
                logger.error(f"{log_prefix} [FETCH]   ✗ Unexpected error parsing thread {thread_id}: {e}")
                logger.error(f"{log_prefix} [FETCH]   Error type: {type(e).__name__}")
                continue

        # Sort threads by most recent message date and trim to requested count.
        # Gmail API orders threads by the date of the matching-sender message, not by
        # overall thread activity — so threads with recent user replies can appear stale.
        # We re-sort by the latest message date across all participants to fix this.
        thread_groups: Dict[str, List[Dict[str, Any]]] = {}  # values contain int fields (message_number, total_in_thread)
        for msg in all_messages:
            tid = msg["thread_id"]
            if tid not in thread_groups:
                thread_groups[tid] = []
            thread_groups[tid].append(msg)

        def _latest_date(messages: List[Dict[str, Any]]) -> dt:
            """Parse RFC 2822 dates from messages, return the most recent one."""
            latest = None
            for m in messages:
                try:
                    parsed = email.utils.parsedate_to_datetime(m["date"])
                    if latest is None or parsed > latest:
                        latest = parsed
                except Exception:
                    continue
            # Use timezone-aware minimum to avoid TypeError when compared with
            # Gmail's timezone-aware dates during sorted()
            return latest or dt.min.replace(tzinfo=timezone.utc)

        # Sort by most recent message date (descending) and keep top N threads
        sorted_threads = sorted(thread_groups.items(), key=lambda x: _latest_date(x[1]), reverse=True)
        top_threads = sorted_threads[:max_results]

        logger.info(f"{log_prefix} [FETCH] Sorting: {len(thread_groups)} threads fetched → keeping top {len(top_threads)} by latest message date")

        # Flatten back to individual messages, preserving message order within each thread
        all_messages = []
        for tid, msgs in top_threads:
            all_messages.extend(sorted(msgs, key=lambda m: m.get("message_number", 1)))

        logger.info(f"{log_prefix} [FETCH] ========== FETCH SUMMARY ==========")
        logger.info(f"{log_prefix} [FETCH] Threads from API: {len(threads)} (over-fetched)")
        logger.info(f"{log_prefix} [FETCH] Successfully processed: {threads_processed}")
        logger.info(f"{log_prefix} [FETCH] Failed/Skipped: {len(threads) - threads_processed}")
        logger.info(f"{log_prefix} [FETCH] Threads after sort+trim: {len(top_threads)} (requested {max_results})")
        logger.info(f"{log_prefix} [FETCH] **TOTAL INDIVIDUAL MESSAGES**: {len(all_messages)}")
        logger.info(f"{log_prefix} ========== FETCH EMAILS END (Success) ==========")

        return all_messages  # Return individual messages from top N threads by activity

    except Exception as e:
        logger.error(f"{log_prefix} [FETCH] ========== FETCH EMAILS FAILED ==========")
        logger.error(f"{log_prefix} [FETCH] ✗ Gmail API error: {str(e)}")
        logger.error(f"{log_prefix} [FETCH] Error type: {type(e).__name__}")
        import traceback
        logger.error(f"{log_prefix} [FETCH] Traceback:\n{traceback.format_exc()}")
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

    logger.debug(f"{log_prefix} Stripping metadata using LLM ({len(email_text)} chars)")

    # System prompt for metadata stripping
    system_prompt = """You are an email cleaning assistant. Your job is to remove email metadata and keep only the actual message content.

**CRITICAL: PRESERVE Thread Separators**
ALWAYS KEEP separators that look like "--- Message X of Y ---" or similar. These indicate multi-message threads and MUST be preserved!

Remove the following:
- Email signatures (e.g., "Sent from my iPhone", "Best regards, John Doe")
- Email headers (From:, To:, Subject:, Date: headers at the top)
- Technical metadata (MIME types, encoding info, message IDs)
- Automatic footers and disclaimers
- Unsubscribe links and promotional text

Keep the following:
- **ALL "--- Message X of Y ---" separators** (CRITICAL - these show conversation flow!)
- Actual message content and conversation
- Hyperlinks that are part of the message
- Questions, answers, and discussion points
- Technical details and code snippets
- Reply context and conversation structure
- Date stamps that are part of thread separators

Return ONLY the cleaned message content WITH all thread separators preserved."""

    user_prompt = f"Clean the following email content:\n\n{email_text}"

    try:
        # Call LLM to strip metadata
        cleaned_text = llm_service.analyze_with_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_id=task_id
        )

        logger.debug(f"{log_prefix} Metadata stripped: {len(email_text)} → {len(cleaned_text)} chars")

        return cleaned_text

    except Exception as e:
        logger.error(f"{log_prefix} Metadata stripping failed: {str(e)}")
        # Return original text if stripping fails
        logger.warning(f"{log_prefix} Using original text (metadata stripping failed)")
        return email_text


def combine_emails(emails: List[Dict[str, str]]) -> str:
    """
    Combine multiple individual messages into single text block for LLM analysis.
    **UPDATED**: Now handles individual messages with thread metadata!

    Args:
        emails: List of individual message dictionaries (each with thread metadata)

    Returns:
        Combined message text with separators and thread context
    """
    combined = []

    for i, email in enumerate(emails, 1):
        combined.append(f"=== MESSAGE {i} ===")
        combined.append(f"Subject: {email['subject']}")
        combined.append(f"From: {email.get('from', 'Unknown')}")
        combined.append(f"Date: {email['date']}")

        # Include thread context (NEW: shows which message in which thread)
        if "thread_id" in email:
            msg_num = email.get("message_number", 1)
            total_in_thread = email.get("total_in_thread", 1)
            combined.append(f"Thread Context: Message {msg_num} of {total_in_thread}")

        # Include old message_count field if present (backward compatibility)
        if "message_count" in email:
            combined.append(f"Messages in thread: {email['message_count']}")

        combined.append(f"\n{email['body']}\n")

    result = "\n".join(combined)

    logger.debug(f"Combined {len(emails)} individual messages into {len(result)} chars")

    return result
