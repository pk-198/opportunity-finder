# Backend - FastAPI Email Analysis Service

<system_context>
FastAPI backend that orchestrates Gmail email fetching, LLM analysis, and result management.
Provides REST API for frontend to trigger analysis and poll for results.

**Key Services**:
- Email fetching via Gmail API (preserve hyperlinks)
- LLM analysis (OpenAI/GROQ switchable)
- In-memory task management with 24hr auto-cleanup
- Batch processing with extensive logging
</system_context>

<critical_notes>
- **workflow.py is the central orchestrator** - all execution flows through it
- **Preserve hyperlinks** when extracting email content
- **180-second timeout** for LLM calls
- **Extensive logging** at every step with timestamps, task_ids, batch numbers
- **In-memory only** - no database or file persistence
- **Error handling**: Skip failed emails, continue processing, return partial results
</critical_notes>

<file_map>
## Core Modules
- `main.py` - FastAPI app, defines 3 endpoints
- `workflow.py` - Central orchestrator controlling entire execution flow
- `email_service.py` - Gmail API integration with extensive logging
- `llm_service.py` - LLM provider abstraction (OpenAI/GROQ)
- `task_manager.py` - In-memory task storage with 24hr cleanup
- `prompts.py` - YAML-based prompt loader

## Configuration
- `config/prompts.yaml` - LLM prompts per sender type
- `config/senders.json` - Sender definitions and metadata
- `.env` - Environment variables (gitignored)
- `.env.example` - Template for setup

## Dependencies
- `requirements.txt` - Python package dependencies
</file_map>

<example>
## API Endpoints

### POST /api/analyze
Starts email analysis task
Request: `{"sender_id": "f5bot", "email_limit": 50, "batch_size": 5}`
Response: `{"task_id": "abc123", "status": "processing"}`

### GET /api/status/{task_id}
Polls for task status and results
Response: `{"task_id": "abc123", "sender_id": "f5bot", "status": "processing", "progress": "2/10", "results": [...]}`
Note: sender_id field added for frontend conditional rendering (Bookface vs F5bot/HARO)

### GET /api/senders
Returns available sender configurations
Response: `{"senders": [{"id": "f5bot", "name": "F5bot Reddit Alerts", ...}]}`

### GET /api/tasks
Returns all tasks in memory (24hr retention)
Response: `{"tasks": [{"task_id": "...", "sender_id": "...", "status": "...", ...}]}`
</example>

<workflow>
## Execution Flow (workflow.py)
1. Receive analysis request via POST /api/analyze
2. Generate unique task_id
3. Launch async task: workflow.run_analysis_workflow()
4. Fetch email threads from Gmail API (email_service.py)
5. Process in sequential batches:
   - Combine threads preserving hyperlinks
   - Load appropriate prompt from prompts.yaml
   - Call LLM with 180s timeout (llm_service.py)
   - Parse and structure results
   - Store in task_manager
6. Update task status after each batch
7. Auto-cleanup after 24 hours
</workflow>

<must_follow_rules>
- All execution MUST flow through workflow.py
- Log every major step with timestamps and task_ids
- Preserve hyperlinks in email content
- Handle errors gracefully - skip failures, continue processing
- Use environment variables from .env
- Never hardcode API keys or credentials
- Keep code minimal and focused
</must_follow_rules>

<sender_types>
## Supported Sender Types (config/senders.json)

### 1. F5bot Reddit Alerts
- **ID**: `f5bot`
- **Email**: `admin@f5bot.com`
- **Purpose**: Reddit keyword monitoring for Dograh AI promotion opportunities
- **Output**: JSON-parsed opportunities across 4 sections (Direct Engagement, Workflow, Content, Blog Topics)

### 2. HARO Opportunities
- **ID**: `haro_main`, `haro_peter`
- **Email**: `haro@helpareporter.com`, `peter@shankman.com`
- **Purpose**: Media opportunities for Dograh AI exposure
- **Output**: JSON-parsed opportunities (Relevant Opportunities, Content to Adapt)

### 3. YC Bookface Forum Digest
- **ID**: `bookface_digest`
- **Email**: `digest@ycombinator.com`
- **Purpose**: Identify growth opportunities and insights from YC internal forum
- **Output**: Markdown format with 5 sections (Growth Hacks, Replicable Content, Commenting, autoRM, Top Threads)
- **Special**: Uses markdown output (not JSON), 1 email/day, frontend renders with BookfaceResults component
</sender_types>
