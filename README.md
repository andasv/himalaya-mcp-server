# himalaya-mcp-server

MCP server that exposes email operations to AI agents (Claude Cowork, Claude Code, etc.) via the [himalaya](https://github.com/pimalaya/himalaya) CLI.

**Read-only by default.** Write and send operations must be explicitly enabled.

## Features

- **Broad himalaya coverage:** accounts, folders, envelopes, messages, flags, attachments, templates
- **Three modes:** read-only (safe default), full (write operations), and dangerzone (sending emails)
- **No destructive operations:** delete, purge, and expunge commands are deliberately excluded (see [Excluded Commands](#excluded-commands))
- **Security-first:** write tools labeled `[DANGER: WRITE]`, send tools labeled `[DANGERZONE: SENDS EMAIL]`
- **No shell injection:** all CLI calls use `subprocess.run()` with list arguments
- **Stdio transport:** works natively with Claude Desktop / Cowork via `claude_desktop_config.json`

## Prerequisites

1. **Python 3.12+**
2. **[uv](https://docs.astral.sh/uv/)** — install with `brew install uv` (macOS) or see [uv docs](https://docs.astral.sh/uv/getting-started/installation/)
3. **[himalaya](https://github.com/pimalaya/himalaya)** — installed and configured with at least one email account

Verify himalaya is working:

```bash
himalaya account list
```

## Installation

Clone the repository:

```bash
git clone https://github.com/andasv/himalaya-mcp-server.git
cd himalaya-mcp-server
uv sync
```

## Usage with Claude Cowork / Claude Desktop

Add the server to your `claude_desktop_config.json`:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

### Read-only mode (default, recommended)

```json
{
  "mcpServers": {
    "himalaya": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/himalaya-mcp-server", "himalaya-mcp-server"]
    }
  }
}
```

### Full mode (enables move, copy, flag, and other write operations)

> **Warning:** Full mode allows the AI agent to move messages, modify flags, create folders, and save drafts. It does **not** allow sending emails.

```json
{
  "mcpServers": {
    "himalaya": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/himalaya-mcp-server", "himalaya-mcp-server"],
      "env": {
        "HIMALAYA_MODE": "full"
      }
    }
  }
}
```

### Dangerzone mode (enables sending emails)

> **Warning:** Dangerzone mode allows the AI agent to **send real emails to real recipients**. This is irreversible. Only enable this if you fully understand the risks.

Dangerzone mode **requires** the `APPROVED_RECIPIENTS` environment variable — a comma-separated list of email addresses the AI is allowed to send to. Sending to any other address will be blocked with a friendly error.

```json
{
  "mcpServers": {
    "himalaya": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/himalaya-mcp-server", "himalaya-mcp-server"],
      "env": {
        "HIMALAYA_MODE": "dangerzone",
        "APPROVED_RECIPIENTS": "alice@example.com,bob@example.com",
        "HIMALAYA_SEND_TIMEOUT": "15"
      }
    }
  }
}
```

After editing the config, **restart Claude Desktop** for changes to take effect.

## Usage with Claude Code

```bash
# Read-only (default)
claude mcp add himalaya -- uv run --project /path/to/himalaya-mcp-server himalaya-mcp-server

# Full mode (write operations, no sending)
claude mcp add --env HIMALAYA_MODE=full himalaya -- uv run --project /path/to/himalaya-mcp-server himalaya-mcp-server

# Dangerzone mode (write + send, with approved recipients)
claude mcp add --env HIMALAYA_MODE=dangerzone --env APPROVED_RECIPIENTS=alice@example.com,bob@example.com himalaya -- uv run --project /path/to/himalaya-mcp-server himalaya-mcp-server
```

## Modes

| Mode | Env var | Tools available |
|------|---------|-----------------|
| **readonly** (default) | `HIMALAYA_MODE=readonly` or unset | List accounts/folders/envelopes, read messages, download attachments, generate templates |
| **full** | `HIMALAYA_MODE=full` | All of the above + move, copy, flag, create folders, save drafts |
| **dangerzone** | `HIMALAYA_MODE=dangerzone` | All of the above + **send emails** |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HIMALAYA_MODE` | No | `readonly` | Operating mode: `readonly`, `full`, or `dangerzone` |
| `APPROVED_RECIPIENTS` | In dangerzone | — | Comma-separated list of email addresses allowed as recipients |
| `HIMALAYA_SEND_TIMEOUT` | No | `15` | Timeout in seconds for send operations. Himalaya retries SMTP 450 errors indefinitely, so this prevents hangs. Keep below 60s (Cowork's tool timeout). |
| `HIMALAYA_LOG_LEVEL` | No | `WARNING` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`. Logs never contain email content or credentials — stderr from himalaya CLI is sanitized before logging. |

## Available Tools

### Read-only tools (always available)

| Tool | Description |
|------|-------------|
| `account_list` | List configured email accounts |
| `folder_list` | List folders/mailboxes |
| `envelope_list` | List message envelopes with search/filter/pagination |
| `envelope_thread` | Get thread view of envelopes |
| `message_read` | Read a message body by ID |
| `message_thread` | Read a full message thread |
| `attachment_download` | Download attachments from a message |
| `template_write` | Generate a blank email template (MML) |
| `template_reply` | Generate a reply template |
| `template_forward` | Generate a forward template |

### Write tools (full and dangerzone modes)

These tools are prefixed with `[DANGER: WRITE]` in their descriptions so the AI agent clearly sees the risk.

| Tool | Description |
|------|-------------|
| `folder_create` | Create a new folder |
| `message_copy` | Copy a message to another folder |
| `message_move` | Move a message to another folder |
| `message_save` | Save a raw MIME message to a folder |
| `flag_add` | Add flags to a message |
| `flag_set` | Replace all flags on a message |
| `flag_remove` | Remove flags from a message |
| `template_save` | Compile MML template and save to folder |

### Send tools (dangerzone mode only)

These tools are prefixed with `[DANGERZONE: SENDS EMAIL]` in their descriptions. They send real emails to real recipients and **cannot be undone**.

| Tool | Description |
|------|-------------|
| `message_send` | Send a raw MIME message |
| `template_send` | Compile MML template and send email |

## Composing and sending emails

Since himalaya's interactive editor commands can't be used in an MCP context, email composition uses the **template pipeline**:

1. **Generate a template** with `template_write`, `template_reply`, or `template_forward`
2. **Edit the template** (the AI fills in To, Subject, body, etc.)
3. **Send** with `template_send` (requires dangerzone mode) or **save as draft** with `template_save` (requires full mode)

### MML template format

```
From: you@example.com
To: recipient@example.com
Subject: Hello

Your message body here.
```

## Excluded Commands

The following himalaya commands are **deliberately not exposed** through this MCP server for safety reasons. Allowing an AI agent to permanently delete emails or folders carries too high a risk of irreversible data loss.

| himalaya command | What it does | Why it's excluded |
|-----------------|-------------|-------------------|
| `folder expunge` | Permanently removes messages marked for deletion | Irreversible bulk deletion |
| `folder purge` | Deletes ALL messages in a folder | Irreversible bulk deletion |
| `folder delete` | Deletes an entire folder and its contents | Irreversible data loss |
| `message delete` | Permanently deletes a single message | Irreversible data loss |

If you need these operations, use the `himalaya` CLI directly.

## Security

- **Read-only by default** — no write tools are even registered unless `HIMALAYA_MODE=full` or `dangerzone`
- **Sending requires dangerzone** — email send tools are isolated in their own mode, separate from other write operations
- **Recipient allowlist** — in dangerzone mode, `APPROVED_RECIPIENTS` must be set; emails can only be sent to explicitly approved addresses
- **No destructive operations** — delete, purge, and expunge commands are excluded entirely
- **Danger labels** — write tools show `[DANGER: WRITE]`, send tools show `[DANGERZONE: SENDS EMAIL]`
- **No shell injection** — all subprocess calls use list arguments, never `shell=True`
- **Input validation** — all parameters are validated before being passed to the CLI
- **Subprocess timeouts** — all CLI calls have a 30-second timeout to prevent hangs
- **himalaya handles auth** — this server never touches credentials; himalaya manages its own auth via its config

## License

MIT
