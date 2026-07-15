# Langfuse Observability Plugin

This plugin ships bundled with Lightning but is **opt-in** — it only loads when
you explicitly enable it.

## Enable

```bash
pip install langfuse
lightning plugins enable observability/langfuse
```

Or check the box in the interactive `lightning plugins` UI.

## Required credentials

Set these in `~/.lightning/.env`:

```bash
LIGHTNING_LANGFUSE_PUBLIC_KEY=pk-lf-...
LIGHTNING_LANGFUSE_SECRET_KEY=sk-lf-...
LIGHTNING_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

Without the SDK or credentials the hooks no-op silently — the plugin fails
open.

## Verify

```bash
lightning plugins list                 # observability/langfuse should show "enabled"
lightning chat -q "hello"              # then check Langfuse for a "Lightning turn" trace
```

## Optional tuning

```bash
LIGHTNING_LANGFUSE_ENV=production       # environment tag
LIGHTNING_LANGFUSE_RELEASE=v1.0.0       # release tag
LIGHTNING_LANGFUSE_SAMPLE_RATE=0.5      # sample 50% of traces
LIGHTNING_LANGFUSE_MAX_CHARS=12000      # max chars per field (default: 12000)
LIGHTNING_LANGFUSE_DEBUG=true           # verbose plugin logging
```

## Disable

```bash
lightning plugins disable observability/langfuse
```
