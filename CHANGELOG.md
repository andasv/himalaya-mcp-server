# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-03-29

### Fixed

- Fix CLI flag ordering: `--folder` and `--account` now placed after subcommand args instead of as global flags, fixing "unexpected argument" errors
- Fix send timeout: configurable via `HIMALAYA_SEND_TIMEOUT` env var (default 15s) to prevent infinite SMTP 450 retry hangs
- Fix Reply-To header bypass: Reply-To now validated against approved recipients
- Fix RFC 5322 header folding: continuation lines properly parsed in recipient validation
- Fix information disclosure: approved recipient list no longer leaked in error messages

### Added

- Detailed logging for send operations and CLI wrapper
- `HIMALAYA_SEND_TIMEOUT` environment variable documentation
- Environment variables reference table in README

## [0.1.0] - 2026-03-29

### Added

- Initial release
- MCP server with stdio transport for Claude Cowork / Claude Desktop / Claude Code
- Three operating modes: read-only (default), full (write operations), and dangerzone (sending emails)
- 10 read-only tools: account_list, folder_list, envelope_list, envelope_thread, message_read, message_thread, attachment_download, template_write, template_reply, template_forward
- 8 write tools (full/dangerzone modes): folder_create, message_copy, message_move, message_save, flag_add, flag_set, flag_remove, template_save
- 2 send tools (dangerzone mode only): message_send, template_send
- Write tools labeled with `[DANGER: WRITE]` prefix
- Send tools labeled with `[DANGERZONE: SENDS EMAIL]` prefix and include confirmation prompts directing the AI to ask the user before sending
- Destructive commands (folder expunge/purge/delete, message delete) deliberately excluded for safety
- Input validation for envelope IDs, folder names, flags, templates, account names, pagination
- Comprehensive test suite
- ruff linting/formatting and mypy strict type checking
