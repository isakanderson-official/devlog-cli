# CLI Reference

> **Note**: After installation (`pip install git+https://github.com/isakanderson-official/devlog-cli.git`), the command is available as `devlog` in your terminal.

The devlog app supports both TUI (interactive) and CLI (command-line) modes.

## Running Modes

**TUI Mode** (default): Run without arguments

```bash
devlog
```

**CLI Mode**: Run with a command

```bash
devlog <command> [options]
```

## CLI Commands

### List Tasks

```bash
# List today's tasks
devlog list

# List tasks for a specific date
devlog list --date tomorrow
devlog list --date yesterday
devlog list --date 2026-03-20

# JSON output
devlog --json list
```

### Add Tasks

```bash
# Add task for today
devlog add "Complete project report"

# Add task for specific date
devlog add "Meeting with team" --date tomorrow
devlog add "Review code" --date 2026-03-25
```

### Mark as Done/Undone

```bash
# Mark task as done (will search all dates if --date not specified)
devlog done <task-id>

# Mark as done on specific date
devlog done <task-id> --date today

# Reopen a completed task
devlog undone <task-id>
```

### Edit Tasks

```bash
# Edit task text
devlog edit <task-id> "Updated task text"

# Edit with specific date
devlog edit <task-id> "New text" --date today
```

### Delete Tasks

```bash
# Delete task
devlog delete <task-id>

# Delete with specific date
devlog delete <task-id> --date today
```

### Search

```bash
# Search all tasks
devlog search "keyword"

# JSON output
devlog --json search "keyword"
```

### Statistics

```bash
# Today's stats
devlog stats

# Weekly stats
devlog stats --range week

# Monthly stats
devlog stats --range month

# JSON output
devlog --json stats --range week
```

### Export to Markdown

```bash
# Export today's tasks
devlog export --date today

# Export all tasks
devlog export

# Save to file
devlog export > tasks.md
```

### Import from Markdown

```bash
# Import from file
devlog import tasks.md

# Import to specific date
devlog import tasks.md --date tomorrow

# Import from stdin
echo "- [ ] New task" | devlog import -
```

## Global Options

```bash
# Specify workspace
devlog -w Work list

# JSON output (place before command)
devlog --json list
devlog --json search "test"
```

## Date Formats

The CLI accepts these date formats:

- `today` or `now` - Current day
- `tomorrow` - Next day
- `yesterday` - Previous day
- `YYYY-MM-DD` - Specific date (e.g., 2026-03-20)

## LLM/Claude Code Usage Examples

### Bulk Add Tasks

```bash
cat << EOF | devlog import -
- [ ] Review PR #123
- [ ] Update documentation
- [ ] Fix bug in login
- [x] Write tests (already done)
EOF
```

### Query and Analyze

```bash
# Get pending task count programmatically
devlog --json list | jq '.tasks | map(select(.done == false)) | length'

# Find all tasks containing "bug"
devlog --json search "bug" | jq '.results[] | .task.text'

# Get completion rate for the week
devlog --json stats --range week | jq '{done: .total_done, total: .total_tasks, rate: (.total_done / .total_tasks * 100)}'
```

### Generate Reports

```bash
# Create weekly report
devlog export > weekly_report_$(date +%Y-%m-%d).md
```

### Pipeline Operations

```bash
# Search, filter, and process
devlog --json search "urgent" | \
  jq -r '.results[] | select(.task.done == false) | .task.text' | \
  while read task; do
    echo "TODO: $task"
  done
```

## Tips for Claude Code Integration

1. **Always use `--json` for programmatic access** - Makes parsing easier
2. **Task IDs are stable** - You can store and reuse them
3. **Idempotent operations** - `done` and `undone` work even if already in that state
4. **Bulk import via stdin** - Perfect for generating task lists from LLM output
5. **Search is workspace-aware** - Automatically searches current workspace
6. **Atomic writes** - Safe for concurrent access (but avoid simultaneous TUI/CLI use)

## Error Handling

All commands return appropriate exit codes:

- `0` - Success
- `1` - Error (invalid date, task not found, etc.)
- `130` - Interrupted (Ctrl-C)

Errors are written to stderr, output to stdout.
