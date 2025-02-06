# Lessons

## User Specified Lessons

- You have a python venv in ./venv. Use it.
- Include info useful for debugging in the program output.
- Read the file before you try to edit it.
- Due to Cursor's limit, when you use `git` and `gh` and need to submit a multiline commit message, first write the message in a file, and then use `git commit -F <filename>` or similar command to commit. And then remove the file. Include "[Cursor] " in the commit message and PR title.

## Cursor learned

- For website image paths, always use the correct relative path (e.g., 'images/filename.png') and ensure the images directory exists
- For search results, ensure proper handling of different character encodings (UTF-8) for international queries
- Add debug information to stderr while keeping the main output clean in stdout for better pipeline integration
- When using seaborn styles in matplotlib, use 'seaborn-v0_8' instead of 'seaborn' as the style name due to recent seaborn version changes
- Use 'gpt-4o' as the model name for OpenAI's GPT-4 with vision capabilities
- When using Jest, a test suite can fail even if all individual tests pass, typically due to issues in suite-level setup code or lifecycle hooks

## Scratchpad Guidelines

- Keep Scratchpad focused on current phase and active tasks
- Include:
  - Current phase from dev plan
  - Active task and its context
  - Current progress with checkboxes
  - Immediate next steps (3-5 items)
  - Recent decisions and important notes
- Update Scratchpad when:
  - Starting new tasks
  - Completing steps
  - Making important decisions
  - Planning next actions
- Clear old tasks when starting new phase/major task
- Use concise, actionable items
- Maintain separation between dev plan (roadmap) and Scratchpad (active work)

# Scratchpad

Current Phase: 2a - Core Pipeline Components & Data Enrichment

Active Task: Garmin Connect API Integration (Priority 1)

- Implementing first enrichment data source
- Focus on sleep and recovery metrics

Current Progress:
[X] Technical design completed
[ ] Implementation Phase

- [ ] Authentication & Config
- [ ] API Client
- [ ] Data Models
- [ ] Service Layer
- [ ] Pipeline Integration

Next Steps:

1. Set up authentication module
2. Create initial API client tests
3. Implement core data models

Decisions/Notes:

- Using async client for better performance
- Implementing caching to respect API limits
- Planning for offline mode support