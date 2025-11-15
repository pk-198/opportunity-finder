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
- **No .env file** - backend URL is hardcoded or uses relative paths
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
- `app/components/SenderSelector.tsx` - Dropdown for sender selection
- `app/components/AnalysisForm.tsx` - Form for email limit and batch size
- `app/components/ProgressBar.tsx` - Visual progress indicator
- `app/components/ResultsDisplay.tsx` - Container for results
- `app/components/OpportunityCard.tsx` - Individual opportunity card

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
- Hardcode backend URL to `http://localhost:8000` or use relative paths
- Keep UI minimal and functional - focus on clarity over aesthetics
- Poll continuously every 15 seconds until task completes
</must_follow_rules>
