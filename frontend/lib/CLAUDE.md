# Frontend Library - API Client

<system_context>
API client module for communicating with the FastAPI backend.
Provides typed functions for all backend endpoints.
</system_context>

<critical_notes>
- **Configurable backend URL**: `NEXT_PUBLIC_API_URL` env var, defaults to `http://localhost:8002`
- **API key auth**: `NEXT_PUBLIC_API_KEY` env var sent as `X-API-Key` header on every request via `commonHeaders`
- **Typed responses**: All functions return properly typed data
- **Error handling**: Throw meaningful errors on API failures
- **Fetch-based**: Uses native fetch API (no axios dependency)
</critical_notes>

<file_map>
## Modules
- `api.ts` - API client with functions for all backend endpoints
</file_map>

<example>
## API Client Functions

```typescript
// Start analysis
export async function startAnalysis(
  senderId: string,
  emailLimit: number,
  batchSize: number
): Promise<{ task_id: string; status: string }> {
  const response = await fetch('http://localhost:8002/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sender_id: senderId, email_limit: emailLimit, batch_size: batchSize })
  });
  return response.json();
}

// Get task status
export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const response = await fetch(`http://localhost:8002/api/status/${taskId}`);
  return response.json();
}

// Get senders
export async function getSenders(): Promise<{ senders: Sender[] }> {
  const response = await fetch('http://localhost:8002/api/senders');
  return response.json();
}
```
</example>

<must_follow_rules>
- Define TypeScript interfaces for all request/response types
- Handle HTTP errors (check response.ok before parsing JSON)
- Use descriptive error messages
- Keep API URL configurable (const at top of file for easy change)
- Never use `any` for return types
</must_follow_rules>
