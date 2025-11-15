# Frontend Components

<system_context>
React components for the email analysis UI. Each component is focused on a single responsibility.
All components use TypeScript with strict typing (no `any` types).
</system_context>

<critical_notes>
- **Minimal and functional** - no over-engineering
- **Strict TypeScript** - define all prop types explicitly
- **Tailwind CSS** for styling - utility-first approach
- Components are stateless where possible, receive data via props
</critical_notes>

<file_map>
## Components
- `SenderSelector.tsx` - Dropdown for selecting email sender
- `AnalysisForm.tsx` - Form inputs for email limit and batch size
- `ProgressBar.tsx` - Visual progress indicator (e.g., "Processing batch 3/10")
- `ResultsDisplay.tsx` - Container that maps opportunities to OpportunityCard
- `OpportunityCard.tsx` - Individual card displaying one opportunity
</file_map>

<example>
## Component Patterns

### SenderSelector
```typescript
interface Sender {
  id: string;
  name: string;
  description: string;
}

interface Props {
  senders: Sender[];
  selectedId: string;
  onSelect: (id: string) => void;
}
```

### OpportunityCard
```typescript
interface Opportunity {
  title: string;
  link: string;
  relevance: string;
  priority: "High" | "Medium" | "Low";
}

interface Props {
  opportunity: Opportunity;
}
```
</example>

<must_follow_rules>
- NEVER use `any` - define interfaces for all props
- Keep components small and focused (single responsibility)
- Use semantic HTML (accessible markup)
- Handle edge cases (empty states, loading states)
- Make hyperlinks clickable (target="_blank" with rel="noopener noreferrer")
</must_follow_rules>
