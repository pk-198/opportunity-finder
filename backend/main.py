"""
FastAPI application for email analysis service.
Provides REST API endpoints for triggering analysis and retrieving results.
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Internal service imports
import workflow
import task_manager

# Configure logging without timestamps (cleaner output)
# Read log level from environment (DEBUG, INFO, WARNING, ERROR)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info(f"Logging configured - level={log_level}")


# Pydantic models for request/response validation
class AnalysisRequest(BaseModel):
    """Request model for starting email analysis."""
    sender_id: str
    email_limit: int = 50
    batch_size: int = 5


class AnalysisResponse(BaseModel):
    """Response model for analysis initiation."""
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Response model for task status queries."""
    task_id: str
    sender_id: str  # Sender identifier (for frontend conditional rendering)
    status: str
    progress: str
    results: List[Dict]
    error: Optional[str] = None


class Sender(BaseModel):
    """Sender configuration model."""
    id: str
    name: str
    email: str
    description: str
    expected_volume: str
    prompt_key: str


class SendersResponse(BaseModel):
    """Response model for senders list."""
    senders: List[Sender]


# Load senders configuration
def load_senders() -> List[Dict]:
    """
    Load sender configurations from config/senders.json.

    Returns:
        List of sender dictionaries

    Raises:
        FileNotFoundError: If senders.json doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    config_dir = Path(__file__).parent / "config"
    senders_file = config_dir / "senders.json"

    if not senders_file.exists():
        logger.error(f"Senders config not found: {senders_file}")
        raise FileNotFoundError(f"Senders config not found: {senders_file}")

    with open(senders_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data['senders'])} senders from config")
    return data["senders"]


# Lifespan context manager for startup/shutdown tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    Runs cleanup on startup and handles graceful shutdown.
    """
    logger.info("========== APPLICATION STARTUP ==========")

    # Cleanup old tasks on startup
    deleted_count = task_manager.cleanup_old_tasks()
    logger.info(f"Startup cleanup: {deleted_count} old tasks deleted")

    yield

    logger.info("========== APPLICATION SHUTDOWN ==========")


# Initialize FastAPI app
app = FastAPI(
    title="Email Analysis API",
    description="Analyzes Gmail emails using LLM and provides actionable insights",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (configure for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Endpoints
@app.post("/api/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks) -> AnalysisResponse:
    """
    Start email analysis workflow.

    Args:
        request: Analysis configuration (sender_id, email_limit, batch_size)

    Returns:
        Task ID and status for tracking

    Raises:
        HTTPException: If sender_id is invalid
    """
    logger.info(f"POST /api/analyze - sender={request.sender_id}, limit={request.email_limit}, batch={request.batch_size}")

    try:
        # Load senders and find matching sender
        senders = load_senders()
        sender = next((s for s in senders if s["id"] == request.sender_id), None)

        if not sender:
            logger.error(f"Invalid sender_id: {request.sender_id}")
            raise HTTPException(status_code=400, detail=f"Invalid sender_id: {request.sender_id}")

        # Create task ID first
        task_id = task_manager.create_task(
            sender_id=sender["id"],
            email_limit=request.email_limit,
            batch_size=request.batch_size
        )

        # Add background task (truly non-blocking)
        background_tasks.add_task(
            workflow.run_analysis_workflow,
            task_id=task_id,
            sender_id=sender["id"],
            sender_email=sender["email"],
            prompt_key=sender["prompt_key"],
            email_limit=request.email_limit,
            batch_size=request.batch_size
        )

        logger.info(f"Analysis started: task_id={task_id}")

        return AnalysisResponse(
            task_id=task_id,
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@app.get("/api/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get status and results for a specific task.

    Args:
        task_id: Unique task identifier

    Returns:
        Task status, progress, and results

    Raises:
        HTTPException: If task_id not found
    """
    logger.info(f"GET /api/status/{task_id}")

    # Retrieve task from task manager
    task = task_manager.get_task(task_id)

    if not task:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    logger.info(f"Task {task_id}: status={task['status']}, progress={task['progress']}")

    return TaskStatusResponse(
        task_id=task["task_id"],
        sender_id=task["sender_id"],
        status=task["status"],
        progress=task["progress"],
        results=task["results"],
        error=task.get("error")
    )


@app.get("/api/senders", response_model=SendersResponse)
async def get_senders() -> SendersResponse:
    """
    Get list of configured email senders.

    Returns:
        List of available senders

    Raises:
        HTTPException: If senders config can't be loaded
    """
    logger.info("GET /api/senders")

    try:
        senders = load_senders()
        logger.info(f"Returning {len(senders)} senders")

        return SendersResponse(senders=senders)

    except Exception as e:
        logger.error(f"Failed to load senders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load senders: {str(e)}")


@app.get("/api/tasks")
async def get_all_tasks():
    """
    Get list of all tasks in memory (24-hour retention).

    Returns:
        List of tasks with metadata (task_id, status, created_at, etc.)
    """
    logger.info("GET /api/tasks")

    try:
        tasks = task_manager.get_all_tasks()

        # Return simplified task list (no full results, just metadata)
        task_list = [
            {
                "task_id": task["task_id"],
                "sender_id": task["sender_id"],
                "status": task["status"],
                "progress": task["progress"],
                "created_at": task["created_at"].isoformat(),
                "updated_at": task["updated_at"].isoformat(),
                "email_limit": task["email_limit"],
                "batch_size": task["batch_size"],
                "result_count": len(task["results"]),
            }
            for task in tasks
        ]

        logger.info(f"Returning {len(task_list)} tasks")
        return {"tasks": task_list}

    except Exception as e:
        logger.error(f"Failed to get tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Status message
    """
    return {"status": "healthy"}


# Run server if executed directly
if __name__ == "__main__":
    logger.info("Starting FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
