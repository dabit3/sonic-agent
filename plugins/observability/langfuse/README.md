# Langfuse Observability Plugin

This plugin ships bundled with Sonic but is **opt-in** — it only loads when
you explicitly enable it.

## Enable

Pick one:

```bash
# Interactive: walks you through credentials + SDK install + enable
sonic tools  # → Langfuse Observability

# Manual
pip install langfuse
sonic plugins enable observability/langfuse
```

## Required credentials

Set these in `~/.sonic/.env` (or via `sonic tools`):

```bash
SONIC_LANGFUSE_PUBLIC_KEY=pk-lf-...
SONIC_LANGFUSE_SECRET_KEY=sk-lf-...
SONIC_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

Without the SDK or credentials the hooks no-op silently — the plugin fails
open.

## Verify

```bash
sonic plugins list                 # observability/langfuse should show "enabled"
sonic chat -q "hello"              # then check Langfuse for a "Sonic turn" trace
```

## Optional tuning

```bash
SONIC_LANGFUSE_ENV=production       # environment tag
SONIC_LANGFUSE_RELEASE=v1.0.0       # release tag
SONIC_LANGFUSE_SAMPLE_RATE=0.5      # sample 50% of traces
SONIC_LANGFUSE_MAX_CHARS=12000      # max chars per field (default: 12000)
SONIC_LANGFUSE_DEBUG=true           # verbose plugin logging
```

## Disable

```bash
sonic plugins disable observability/langfuse
```
