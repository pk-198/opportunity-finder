# Backend Configuration Files

<system_context>
Configuration files that define sender metadata and LLM prompts.
These files make the system config-driven - changes don't require code updates.
</system_context>

<critical_notes>
- **prompts.yaml** contains all LLM prompts keyed by sender type
- **senders.json** defines available email senders and their metadata
- Prompts use `{email_content}` placeholder for dynamic content injection
- Each sender references a prompt_key that maps to prompts.yaml
</critical_notes>

<file_map>
## Configuration Files
- `prompts.yaml` - LLM system and user prompts per sender type
- `senders.json` - Sender definitions (id, name, email, description, prompt_key)
</file_map>

<example>
## Sender Definition (senders.json)
```json
{
  "id": "f5bot",
  "name": "F5bot Reddit Alerts",
  "email": "admin@f5bot.com",
  "prompt_key": "f5bot_reddit"
}
```

## Prompt Structure (prompts.yaml)
```yaml
f5bot_reddit:
  system_prompt: |
    You are an expert at analyzing Reddit posts...
  user_prompt: |
    Analyze the following Reddit posts: {email_content}
```
</example>

<must_follow_rules>
- Keep prompts focused and specific to sender type
- Always use `{email_content}` placeholder in user_prompt
- Ensure sender.prompt_key matches a key in prompts.yaml
- Document expected output format in prompts
</must_follow_rules>
