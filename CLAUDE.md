# Gmail Email Analysis Automation - Project Context

<system_context>
This is an internal tool that analyzes Gmail emails from specific senders (F5bot Reddit alerts, HARO requests) using LLM prompts and displays actionable insights in real-time on a web interface.

**Purpose**: Identify engagement opportunities where Dograh AI can be promoted or provide value.

**Tech Stack**:
- Backend: FastAPI (Python)
- Frontend: Next.js (TypeScript)
- LLM: OpenAI GPT-4o-mini or GROQ (switchable)
- Email: Gmail API with OAuth
- Storage: In-memory only (24hr auto-cleanup)
</system_context>

<critical_notes>
- **Write MINIMAL, ELEGANT code** - no extra features
- **STATELESS**: In-memory only, no database
- **Preserve all hyperlinks** during email extraction
- **180-second timeout** per LLM call
- **Batch processing**: Default 5 emails per batch
- **Polling-based**: Frontend polls every 15 seconds
- **Config-driven**: Prompts and senders in YAML/JSON files
- **User runs the app**: Always provide instructions for user to test
</critical_notes>

<file_map>
## Backend Structure
- `backend/main.py` - FastAPI app with 3 endpoints
- `backend/workflow.py` - Central orchestrator (ALL execution flow)
- `backend/email_service.py` - Gmail API integration
- `backend/llm_service.py` - LLM calls (OpenAI/GROQ)
- `backend/task_manager.py` - In-memory task storage
- `backend/prompts.py` - Prompt loader from YAML
- `backend/config/prompts.yaml` - LLM prompts per sender
- `backend/config/senders.json` - Sender definitions
- `backend/.env` - Secrets (gitignored)
- `backend/.env.example` - Template for setup

## Frontend Structure
- `frontend/app/page.tsx` - Main form page
- `frontend/app/analysis/page.tsx` - Results page with polling
- `frontend/app/components/` - React components
- `frontend/lib/api.ts` - API client (hardcoded backend URL)
</file_map>

<workflow>
## Execution Flow
1. User selects sender from dropdown (e.g., "F5bot Alerts")
2. User inputs: number of emails (default: 50), batch size (default: 5)
3. Frontend POSTs to `/api/analyze`, receives `{task_id: "XYZ123"}`
4. Frontend redirects to `/analysis?task_id=XYZ123`
5. Backend executes via `workflow.py::run_analysis_workflow()`:
   - Fetch email threads from Gmail (preserve hyperlinks)
   - Process in sequential batches
   - For each batch: combine threads → analyze with LLM → parse output
   - Store results in memory with task_id
   - Log every step
6. Frontend polls `/api/status/XYZ123` every 15 seconds
7. Results appear incrementally as batches complete
8. Backend auto-deletes task data after 24 hours
</workflow>


<must_follow_rules>
## MISSION CRITICAL RULES
1. **Code with elegance** - Write clean and minimal code. Do not write anything extra or extra fetures.
2. **Clarify ambiguity** - Favor asking follow-up questions to ensure clear understanding of requirements before implementation.
3. **Preserve existing functionality** - NEVER reduce the scope of existing features/behaviors unless explicitly instructed to do so.
4. **create nested CLAUDE.md**
 - ULTRA CRITICAL: cladue.md files shall be created in every folder and subfolder where you have written any code. It should contain an updated context and overview of the code in that subfolder. Keep updating it if any code changes are made. 
5. **keep updating all CLAUDE.md files- it is a living documentation**
 - ULTRA CRITICAL: Treat all CLAUDE.md files as living API documentation for your future self. Always check for relevant CLAUDE.md files and DEFINITELY UPDATE them when changes impact their accuracy.

6. **Add good comments everywhere** -  add comments in your code to make it better documented. definitely add a one line comment in each file saying what it does and another comment on each function or class saying what it does. when using  external functions and  external libraries , then add a small 4-5 word comment on what it does as well

7. **Output user's next steps and testing instructions** -at every step make sure to output the next steps for the user like adding details in env file or setting up a supabase account etc.  And also share clear instructions on how the user can test the work so far.

8. **Write minimal code** -at every step make sure to write as little code as possible, do not write code for the sake of writing and defeintely dont write a lit of code - only write code thats enough to serve the given use case.

9.  **NEVER use `any` types** - Request user approval if tempted
10. **Update on change** - If code changes affect docs, update immediately- update and create claude.md for folders and subfolders. also update readme.md for context and any updates. When making updates , remove any old context that got changed.
11. **Maintain CHANGES.md** :- maintain a changes.md where you keep logging in the changes you make along with the reason why 

</must_follow_rules>