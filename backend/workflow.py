"""
Central workflow orchestrator for email analysis.
ALL execution flows through this module - coordinates email fetching, LLM analysis, and result storage.
"""

import logging
import asyncio
from typing import Dict, List
from datetime import datetime

# Internal service imports
import task_manager
import email_service
import llm_service
import prompts

# Configure logging for workflow operations
logger = logging.getLogger(__name__)


async def run_analysis_workflow(
    task_id: str,
    sender_id: str,
    sender_email: str,
    prompt_key: str,
    email_limit: int,
    batch_size: int
) -> None:
    """
    Central orchestrator - executes complete email analysis workflow.

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
        logger.info(f"[{task_id}] Loading prompts for key: {prompt_key}")
        prompt_data = prompts.get_prompt(prompt_key)
        system_prompt = prompt_data["system_prompt"]

        # Step 4: Process each batch sequentially
        for batch_num, batch in enumerate(batches, 1):
            logger.info(f"[{task_id}] ===== Processing Batch {batch_num}/{total_batches} =====")

            try:
                # Combine threads in batch preserving hyperlinks
                logger.info(f"[{task_id}] Combining {len(batch)} threads")
                combined_emails = email_service.combine_emails(batch)

                # Strip metadata using LLM (LLM Call #1)
                logger.info(f"[{task_id}] Stripping metadata (LLM Call #1)")
                cleaned_emails = email_service.strip_metadata_with_llm(
                    email_text=combined_emails,
                    task_id=task_id
                )

                # Format user prompt with cleaned email content
                user_prompt = prompts.format_user_prompt(prompt_key, cleaned_emails)

                # Call LLM for analysis (LLM Call #2) - 180s timeout
                logger.info(f"[{task_id}] Analyzing content (LLM Call #2)")
                llm_response = llm_service.analyze_with_llm(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    task_id=task_id
                )

                # Parse markdown to JSON (LLM Call #3)
                logger.info(f"[{task_id}] Parsing markdown to JSON (LLM Call #3)")
                parsed_response = llm_service.parse_markdown_to_json(
                    markdown_text=llm_response,
                    task_id=task_id
                )

                # Store batch result
                batch_result = {
                    "batch_number": batch_num,
                    "total_batches": total_batches,
                    "threads_in_batch": len(batch),
                    "analysis": parsed_response,  # Store parsed JSON
                    "raw_markdown": llm_response,  # Also keep raw markdown
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
        logger.info(f"[{task_id}] All batches processed - elapsed: {elapsed:.1f}s")

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


def start_analysis(
    sender_id: str,
    sender_email: str,
    prompt_key: str,
    email_limit: int,
    batch_size: int
) -> str:
    """
    Start email analysis workflow asynchronously.
    Creates task and launches background processing.

    Args:
        sender_id: Sender identifier
        sender_email: Email address to analyze
        prompt_key: Prompt configuration key
        email_limit: Maximum emails to process
        batch_size: Emails per batch

    Returns:
        Task ID for tracking progress
    """
    # Create task for tracking
    task_id = task_manager.create_task(sender_id, email_limit, batch_size)

    logger.info(f"[{task_id}] Analysis started - launching async workflow")

    # Launch workflow in background using asyncio
    asyncio.create_task(
        run_analysis_workflow(
            task_id=task_id,
            sender_id=sender_id,
            sender_email=sender_email,
            prompt_key=prompt_key,
            email_limit=email_limit,
            batch_size=batch_size
        )
    )

    return task_id
