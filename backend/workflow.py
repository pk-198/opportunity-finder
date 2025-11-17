"""
Central workflow orchestrator for email analysis.
ALL execution flows through this module - coordinates email fetching, LLM analysis, and result storage.
"""

import logging
from typing import Dict, List
from datetime import datetime

# Internal service imports
import task_manager
import email_service
import llm_service
import prompts

# Configure logging for workflow operations
logger = logging.getLogger(__name__)


def run_analysis_workflow(
    task_id: str,
    sender_id: str,
    sender_email: str,
    prompt_key: str,
    email_limit: int,
    batch_size: int
) -> None:
    """
    Central orchestrator - executes complete email analysis workflow.

    NOTE: This is a SYNCHRONOUS function (not async) because it contains blocking I/O:
    - Gmail API calls (email_service.fetch_emails)
    - LLM API calls (llm_service.analyze_with_llm)
    - File I/O operations

    FastAPI's BackgroundTasks runs this in a thread pool for non-blocking execution.

    Workflow steps:
    1. Fetch email THREADS from Gmail
    2. Split into batches
    3. For each batch:
       - Combine thread emails preserving hyperlinks
       - Strip metadata with LLM (LLM Call #1)
       - Analyze with main LLM (LLM Call #2)
       - Parse markdown to JSON (LLM Call #3)
       - Store results
    4. Update task status after each batch
    5. Mark task as completed or failed

    Args:
        task_id: Unique task identifier for tracking
        sender_id: Sender identifier (e.g., "f5bot")
        sender_email: Email address to fetch from
        prompt_key: Prompt key for LLM analysis
        email_limit: Maximum number of THREADS to process
        batch_size: Number of THREADS per batch
    """
    logger.info(f"[{task_id}] ========== WORKFLOW START ==========")
    logger.info(f"[{task_id}] Config: sender={sender_id}, email={sender_email}, limit={email_limit}, batch={batch_size}")

    start_time = datetime.now()

    try:
        # Step 1: Fetch emails from Gmail
        logger.info(f"[{task_id}] Step 1: Fetching emails from Gmail")
        emails = email_service.fetch_emails(
            sender_email=sender_email,
            max_results=email_limit,
            task_id=task_id
        )

        if not emails:
            logger.warning(f"[{task_id}] No emails found - marking as completed")
            task_manager.update_task(
                task_id,
                status="completed",
                progress="0/0",
                error="No emails found from this sender"
            )
            return

        logger.info(f"[{task_id}] Fetched {len(emails)} emails successfully")

        # Step 2: Split emails into batches
        batches = _create_batches(emails, batch_size)
        total_batches = len(batches)
        logger.info(f"[{task_id}] Split into {total_batches} batches of size {batch_size}")

        # Step 3: Load prompts for LLM
        logger.debug(f"[{task_id}] Loading prompts for key: {prompt_key}")
        prompt_data = prompts.get_prompt(prompt_key)
        system_prompt = prompt_data["system_prompt"]

        # Step 4: Process each batch sequentially
        for batch_num, batch in enumerate(batches, 1):
            logger.info(f"[{task_id}] ===== Processing Batch {batch_num}/{total_batches} =====")

            try:
                # Combine threads in batch preserving hyperlinks
                logger.debug(f"[{task_id}] Combining {len(batch)} threads")
                combined_emails = email_service.combine_emails(batch)

                # Strip metadata using LLM (LLM Call #1)
                logger.info(f"[{task_id}] Stripping metadata (LLM Call #1)")
                cleaned_emails = email_service.strip_metadata_with_llm(
                    email_text=combined_emails,
                    task_id=task_id
                )

                # Format user prompt with cleaned email content
                logger.debug(f"[{task_id}] Formatting user prompt with cleaned content")
                user_prompt = prompts.format_user_prompt(prompt_key, cleaned_emails)

                # Call LLM for analysis (LLM Call #2) - 180s timeout
                logger.info(f"[{task_id}] Analyzing content (LLM Call #2)")
                llm_response = llm_service.analyze_with_llm(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    task_id=task_id
                )

                # Save raw LLM response to file for debugging
                import os
                from pathlib import Path
                debug_dir = Path(__file__).parent / "debug_outputs"
                debug_dir.mkdir(exist_ok=True)
                debug_file = debug_dir / f"{task_id}_batch{batch_num}_llm_call2_raw.txt"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(f"=== LLM Call #2 Raw Output ===\n")
                    f.write(f"Task ID: {task_id}\n")
                    f.write(f"Batch: {batch_num}/{total_batches}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Response Length: {len(llm_response)} chars\n")
                    f.write(f"\n{'='*60}\n\n")
                    f.write(llm_response)
                logger.info(f"[{task_id}] Raw LLM output saved to: {debug_file}")

                # Parse markdown to JSON (LLM Call #3)
                logger.info(f"[{task_id}] Parsing markdown to JSON (LLM Call #3)")

                # Save input to parsing LLM
                debug_file_parse_input = debug_dir / f"{task_id}_batch{batch_num}_llm_call3_input.txt"
                with open(debug_file_parse_input, "w", encoding="utf-8") as f:
                    f.write(f"=== LLM Call #3 Input (Markdown to be parsed) ===\n")
                    f.write(f"Task ID: {task_id}\n")
                    f.write(f"Batch: {batch_num}/{total_batches}\n")
                    f.write(f"Input Length: {len(llm_response)} chars\n")
                    f.write(f"\n{'='*60}\n\n")
                    f.write(llm_response)
                logger.info(f"[{task_id}] Parsing input saved to: {debug_file_parse_input}")

                parsed_response = llm_service.parse_markdown_to_json(
                    markdown_text=llm_response,
                    task_id=task_id
                )

                # Save final parsed JSON output
                debug_file_parsed = debug_dir / f"{task_id}_batch{batch_num}_llm_call3_output.json"
                with open(debug_file_parsed, "w", encoding="utf-8") as f:
                    f.write(parsed_response)
                logger.info(f"[{task_id}] Parsing output saved to: {debug_file_parsed}")

                # Store batch result with original emails for drawer
                batch_result = {
                    "batch_number": batch_num,
                    "total_batches": total_batches,
                    "threads_in_batch": len(batch),
                    "analysis": parsed_response,  # Store parsed JSON
                    "raw_markdown": llm_response,  # Also keep raw markdown
                    "original_emails": [  # Store original emails for cross-checking
                        {
                            "subject": email.get("subject", "No Subject"),
                            "body": email.get("body", ""),
                            "date": email.get("date", "Unknown Date")
                        }
                        for email in batch
                    ],
                    "processed_at": datetime.now().isoformat()
                }

                task_manager.add_result(task_id, batch_result)

                # Update progress
                progress = f"{batch_num}/{total_batches}"
                task_manager.update_task(task_id, progress=progress)

                logger.info(f"[{task_id}] Batch {batch_num} completed - progress: {progress}")

            except Exception as e:
                logger.error(f"[{task_id}] Batch {batch_num} failed: {str(e)}")

                # Store error but continue processing
                error_result = {
                    "batch_number": batch_num,
                    "total_batches": total_batches,
                    "threads_in_batch": len(batch),
                    "error": str(e),
                    "processed_at": datetime.now().isoformat()
                }
                task_manager.add_result(task_id, error_result)

                # Continue with next batch
                continue

        # Step 5: Mark task as completed
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{task_id}] All batches processed successfully - elapsed: {elapsed:.1f}s")

        task_manager.update_task(
            task_id,
            status="completed",
            progress=f"{total_batches}/{total_batches}"
        )

        logger.info(f"[{task_id}] ========== WORKFLOW COMPLETE ==========")

    except Exception as e:
        # Handle workflow-level errors
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"[{task_id}] Workflow failed after {elapsed:.1f}s: {str(e)}")

        task_manager.update_task(
            task_id,
            status="failed",
            error=str(e)
        )

        logger.info(f"[{task_id}] ========== WORKFLOW FAILED ==========")


def _create_batches(items: List, batch_size: int) -> List[List]:
    """
    Split list into batches of specified size.

    Args:
        items: List to split
        batch_size: Maximum items per batch

    Returns:
        List of batches (each batch is a list)
    """
    batches = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batches.append(batch)

    return batches
