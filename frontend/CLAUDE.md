# Frontend - Next.js Email Analysis UI

<system_context>
Next.js frontend providing a minimal, functional UI for triggering email analysis
and viewing results in real-time via polling.

**Key Features**:
- Sender selection dropdown
- Analysis configuration form
- Real-time progress polling (15-second intervals)
- Incremental results display
- URL-based state management (task_id in query params)
</system_context>

<critical_notes>
- **Password-gated** - `AuthGate` component in `layout.tsx` requires password from `NEXT_PUBLIC_ACCESS_PASSWORD` env var. Uses sessionStorage (clears on tab close).
- **API key auth** - All API calls include `X-API-Key` header from `NEXT_PUBLIC_API_KEY` env var.
- **Configurable backend URL** - `NEXT_PUBLIC_API_URL` env var (defaults to `http://localhost:8002` if unset).
- **`.env.local`** - holds `NEXT_PUBLIC_ACCESS_PASSWORD`, `NEXT_PUBLIC_API_KEY`, `NEXT_PUBLIC_API_URL` (not committed to git)
- **URL-based state** - task_id in URL params, not sessionStorage
- **15-second polling** - continuous status checks until completion
- **Minimal UI** - functional, not fancy (Tailwind CSS for basic styling)
- **TypeScript strict mode** - NEVER use `any` types
</critical_notes>

<file_map>
## Pages
- `app/page.tsx` - Main form page (sender selection, configuration)
- `app/analysis/page.tsx` - Results page with polling and display

## Components
- `app/components/AuthGate.tsx` - Password gate wrapping all pages (sessionStorage-based)
- `app/components/SenderSelector.tsx` - Dropdown for sender selection
- `app/components/AnalysisForm.tsx` - Form for email limit and batch size
- `app/components/ProgressBar.tsx` - Visual progress indicator
- `app/components/ResultsDisplay.tsx` - **Conditional renderer** (BookfaceResults for bookface_digest, OpportunityCard for F5bot/HARO)
- `app/components/OpportunityCard.tsx` - **Individual opportunity card** (recursive JSON renderer for F5bot/HARO)
- `app/components/BookfaceResults.tsx` - **Markdown parser for Bookface** (5 collapsible sections, priority badges)
- `app/components/EmailDrawer.tsx` - **Original emails drawer** (right side, shows email content for cross-checking)
- `app/components/TaskListDrawer.tsx` - **Task history drawer** (home page, shows all tasks in memory)

## API Client
- `lib/api.ts` - API client for backend communication (fetch wrapper)
</file_map>

<workflow>
## User Flow
1. User lands on `/` (main page)
2. Selects sender from dropdown (fetched from `/api/senders`)
3. Optionally adjusts email limit and batch size (defaults: 50, 5)
4. Clicks "Analyze Emails"
5. Frontend POSTs to `/api/analyze`
6. Receives `{task_id: "XYZ123"}` and redirects to `/analysis?task_id=XYZ123`
7. Results page polls `/api/status/XYZ123` every 15 seconds
8. Displays progress bar and incremental results
9. Shows completion when status = "completed"
</workflow>

<example>
## API Client Usage (lib/api.ts)
```typescript
// Start analysis
const result = await startAnalysis("f5bot", 50, 5);
// Returns: { task_id: "abc123", status: "processing" }

// Poll status
const status = await getTaskStatus("abc123");
// Returns: { status: "processing", progress: "2/10", results: [...] }

// Get senders
const senders = await getSenders();
// Returns: { senders: [{id: "f5bot", name: "F5bot", ...}] }
```
</example>

<must_follow_rules>
- NEVER use TypeScript `any` - define proper types/interfaces
- Always handle loading and error states
- Use URL params for task_id (enables page refresh without losing state)
- Backend URL configurable via `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8002`)
- Keep UI minimal and functional - focus on clarity over aesthetics
- Poll continuously every 15 seconds until task completes
</must_follow_rules>

<recent_changes>
## Frontend Reorganization (2025-01-16)

### Section-Based Results Display
**Changed**: Results are now organized by SECTION (not batch)
- **Before**: Batch 1 → Sections → Opportunities, Batch 2 → Sections → Opportunities
- **After**: Section 1 → All opportunities from all batches, Section 2 → All opportunities from all batches

**Files Modified**:
- `ResultsDisplay.tsx` - Added `aggregateBySection()` function to group by section
- `OpportunityCard.tsx` - Simplified to display single opportunity (not full batch)

### OpportunityCard Simplification
**Changed**: Component now displays individual opportunity
- **Props**: `opportunity: any`, `showBatchInfo?: boolean` (was `result: BatchResult`)
- **Rendering**: Recursive `renderObjectAsText()` dumps all JSON fields as plain text
- **Filters**: Skips `priority` (shown in badge) and `_*` metadata fields
- **Footer**: Optional batch info (From Batch X of Y • timestamp)

### Type Fixes
**Fixed**: API type mismatch
- `BatchResult.emails_in_batch` renamed to `thread_count_in_batch` (matches backend)
- Added inline comments to all type fields

### Gmail API Transport Fix
**Fixed**: Gmail API timeout issues
- Removed `http` parameter from `build()` (was causing "mutually exclusive" error)
- Simplified to `build("gmail", "v1", credentials=creds)` only

### YC Bookface Support (2025-01-16)
**Added**: New sender type with markdown-based output and custom rendering

**New Component**: `BookfaceResults.tsx`
- Parses markdown output into 5 sections (Growth Hacks, Replicable Content, Commenting, autoRM, Top Threads)
- Collapsible section panels with emoji headers
- Priority badges (High/Medium/Low)
- Special rendering for TOP 2 THREADS (numbered list format)
- Item cards with clickable links

**Conditional Rendering**: `ResultsDisplay.tsx`
- Checks `senderId === 'bookface_digest'`
- Renders `BookfaceResults` for Bookface emails
- Renders existing `OpportunityCard` display for F5bot/HARO

**API Enhancement**: `TaskStatus` interface
- Added `sender_id: string` field for conditional rendering
</recent_changes>

<sender_types>
## Supported Sender Types

### 1. F5bot Reddit Alerts (`f5bot`)
- **Display**: OpportunityCard component (JSON-based)
- **Sections**: Direct Engagement, Workflow Opportunities, Content to Adapt, Blog Topics
- **Format**: Structured JSON parsed into opportunity cards

### 2. HARO Opportunities (`haro_main`, `haro_peter`)
- **Display**: OpportunityCard component (JSON-based)
- **Sections**: Relevant Opportunities, Content to Adapt
- **Format**: Structured JSON parsed into opportunity cards

### 3. YC Bookface Forum Digest (`bookface_digest`)
- **Display**: BookfaceResults component (Markdown-based)
- **Sections**: Growth Hacks & Learnings, Replicable Content Ideas, Commenting Opportunities, autoRM Relevant Threads, Top 2 Threads Collection
- **Format**: Markdown with emoji headers, parsed into collapsible sections
- **Special**: Priority badges, numbered list for Top Threads, link extraction from hyperlinks
</sender_types>
