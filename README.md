# Sonic Agent

<p align="center">
  <a href="https://github.com/dabit3/sonic-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/NousResearch/hermes-agent"><img src="https://img.shields.io/badge/Fork%20of-Sonic%20Agent-blueviolet?style=for-the-badge" alt="Fork of Hermes Agent"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
</p>

> Sonic Agent is a fork of [Sonic Agent](https://github.com/NousResearch/hermes-agent) from [Nous Research](https://nousresearch.com). This fork is tuned for one property: speed. It optimizes startup time, time to first token, and streaming speed. In some cases it removes features to get this speed. The upstream documentation is at [lightning-agent.nousresearch.com/docs](https://lightning-agent.nousresearch.com/docs/).

Sonic keeps the full agent toolkit: terminal, skills, memory, messaging gateway, and cron. It treats each millisecond between your Enter key and the first token on the screen as a defect.

## Speed design

Latency in an agent comes from four places. These places are process startup, request setup, prefill (the tokens you send), and decode (the tokens you get back). Sonic reduces the latency of all four.

| Layer | What Sonic does |
|-------|-----------------|
| **Process startup** | Sonic loads large model catalogs and multi-MB metadata caches only on demand. The CLI starts about 35% faster than upstream. Large subsystems load only when you use them. |
| **Request setup** | Sonic opens the DNS, TCP, and TLS connection to your provider in the background at startup. TCP keepalive holds the connection open. Your first request streams immediately, without a handshake. |
| **Prefill (input tokens)** | The default **speed profile** removes the per-turn prompt extras (memory and skill nudges) that make each request larger. It also uses prompt caching on the provider side. Fewer input tokens give a faster first output token. |
| **Decode (output tokens)** | Sonic streams everywhere and caches responses. The output length limit is 4096 tokens by default, so the model answers in short form. The optional retry limit (`speed.api_max_retries`) makes Sonic fail over quickly instead of waiting for a slow provider. |

These settings ship as the `speed` profile in `~/.sonic/config.yaml`. Each option is visible to you. To restore stock upstream behavior, set `speed.enabled: false`:

```yaml
speed:
  enabled: true
  max_tokens: 4096          # output cap — fast answers over long essays
  api_max_retries: 0        # >0 caps retries for fast failover (opt-in)
  disable_memory_nudges: true
  disable_skill_nudges: true
  prewarm_connection: true  # background TLS handshake at startup
```

**Pick a fast model.** The model controls most of the speed. A small model on a fast provider is faster than a frontier reasoning model. Examples are `openai/gpt-4o-mini`, a Flash, Haiku, or nano class model, or any model on high-throughput infrastructure. To change the model at any time, run `sonic model`.

You can use any model. The options include [OpenRouter](https://openrouter.ai) (200+ models), [Nous Portal](https://portal.nousresearch.com), [NovitaAI](https://novita.ai), [NVIDIA NIM](https://build.nvidia.com), [z.ai/GLM](https://z.ai), [Kimi/Moonshot](https://platform.moonshot.ai), [MiniMax](https://www.minimax.io), [Hugging Face](https://huggingface.co), OpenAI, and your own endpoint. To change the model, run `sonic model`. No code changes are necessary.

<table>
<tr><td><b>A real terminal interface</b></td><td>A full TUI with multiline editing, slash-command autocomplete, conversation history, interrupt-and-redirect, and streaming tool output.</td></tr>
<tr><td><b>Lives where you do</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, and the CLI, all from one gateway process. It transcribes voice memos and continues one conversation across platforms.</td></tr>
<tr><td><b>A closed learning loop</b></td><td>The agent curates its own memory and gets periodic nudges. It writes new skills after complex tasks, and skills improve themselves during use. FTS5 session search with LLM summarization gives recall across sessions. <a href="https://github.com/plastic-labs/honcho">Honcho</a> gives dialectic user modeling. Sonic is compatible with the <a href="https://agentskills.io">agentskills.io</a> open standard.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>A built-in cron scheduler with delivery to any platform. Daily reports, nightly backups, and weekly audits run unattended. You write them in natural language.</td></tr>
<tr><td><b>Delegates and parallelizes</b></td><td>Sonic can start isolated subagents for parallel work. Python scripts can call tools through RPC. This collapses a multi-step pipeline into one turn with no context cost.</td></tr>
<tr><td><b>Runs anywhere, not only your laptop</b></td><td>Six terminal backends: local, Docker, SSH, Singularity, Modal, and Daytona. Daytona and Modal give serverless persistence. The environment of the agent hibernates when it is idle and wakes on demand, at almost no cost between sessions. Sonic runs on a $5 VPS or on a GPU cluster.</td></tr>
<tr><td><b>Research-ready</b></td><td>Batch trajectory generation and trajectory compression, to train the next generation of tool-calling models.</td></tr>
</table>

---

## Quick Install

### Linux, macOS, WSL2, Termux

```bash
curl -fsSL https://raw.githubusercontent.com/dabit3/sonic-agent/main/scripts/install.sh | bash
```

### Windows (native, PowerShell)

> **Heads up:** Native Windows runs Sonic without WSL — the CLI, gateway, TUI, and tools all work natively. If you'd rather use WSL2, the Linux and macOS one-liner above works there too. Found a bug? Please [file an issue](https://github.com/dabit3/sonic-agent/issues).

Run this command in PowerShell:

```powershell
iex (irm https://raw.githubusercontent.com/dabit3/sonic-agent/main/scripts/install.ps1)
```

The installer adds uv, Python 3.11, Node.js, ripgrep, ffmpeg, and a portable Git Bash. The portable Git Bash is MinGit. The installer unpacks it to `%LOCALAPPDATA%\sonic\git`, without admin rights, and keeps it isolated from a system Git installation. Sonic runs shell commands with this bundled Git Bash.

If Git is already installed, the installer finds it and uses it. If Git is not installed, the installer downloads MinGit (about 45 MB). MinGit does not change a system Git installation.

> **Android and Termux:** The tested manual path is in the [Termux guide](https://lightning-agent.nousresearch.com/docs/getting-started/termux). On Termux, Sonic installs the `.[termux]` extra, because the full `.[all]` extra pulls voice dependencies that Android does not support.
>
> **Windows:** Native Windows is fully supported — the PowerShell command above installs everything. If you'd rather use WSL2, the Linux command works there too. A native Windows installation goes in `%LOCALAPPDATA%\sonic`. A WSL2 installation goes in `~/.sonic`, as on Linux. One Sonic feature needs WSL2: the browser-based dashboard chat pane, because it uses a POSIX PTY. The classic CLI and the gateway both run natively.

After the installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
sonic              # start chatting
```

---

## Getting Started

```bash
sonic              # Interactive CLI — start a conversation
sonic model        # Choose your LLM provider and model
sonic tools        # Configure which tools are enabled
sonic config set   # Set individual config values
sonic gateway      # Start the messaging gateway (Telegram, Discord, and more)
sonic setup        # Run the full setup wizard (configures everything at once)
sonic claw migrate # Migrate from OpenClaw (if coming from OpenClaw)
sonic update       # Update to the latest version
sonic doctor       # Diagnose problems
```

**[Full documentation](https://lightning-agent.nousresearch.com/docs/)**

---

## One subscription for keys — Nous Portal

Sonic works with any provider, and that does not change. [Nous Portal](https://portal.nousresearch.com) is an alternative to five separate API keys for the model, web search, image generation, text-to-speech, and a cloud browser. One subscription covers all of them:

- **300+ models** — select one with `/model <name>`
- **Tool Gateway** — web search (Firecrawl), image generation (FAL), text-to-speech (OpenAI), and a cloud browser (Browser Use). Your subscription routes all of them. No other accounts are necessary.

From a new installation, one command is enough:

```bash
sonic setup --portal
```

This command logs you in with OAuth, sets Nous as your provider, and turns on the Tool Gateway. To see the current status, run `sonic portal status`. The details are on the [Tool Gateway docs page](https://lightning-agent.nousresearch.com/docs/user-guide/features/tool-gateway).

You can still use your own key for each tool. The gateway works per backend, not for all backends together.

---

## CLI and messaging reference

Sonic has two entry points. To start the terminal UI, run `sonic`. To use Telegram, Discord, Slack, WhatsApp, Signal, or Email, run the gateway. In a conversation, both interfaces share many slash commands.

| Action | CLI | Messaging platforms |
|---------|-----|---------------------|
| Start chatting | `sonic` | Run `sonic gateway setup` and `sonic gateway start`. Then send the bot a message |
| Start a new conversation | `/new` or `/reset` | `/new` or `/reset` |
| Change model | `/model [provider:model]` | `/model [provider:model]` |
| Set a personality | `/personality [name]` | `/personality [name]` |
| Retry or undo the last turn | `/retry`, `/undo` | `/retry`, `/undo` |
| Compress context or see usage | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]` |
| Browse skills | `/skills` or `/<skill-name>` | `/<skill-name>` |
| Interrupt the current work | `Ctrl+C`, or send a new message | `/stop`, or send a new message |
| Platform-specific status | `/platforms` | `/status`, `/sethome` |

For the full command lists, read the [CLI guide](https://lightning-agent.nousresearch.com/docs/user-guide/cli) and the [Messaging Gateway guide](https://lightning-agent.nousresearch.com/docs/user-guide/messaging).

---

## Documentation

All documentation is at **[lightning-agent.nousresearch.com/docs](https://lightning-agent.nousresearch.com/docs/)**:

| Section | Contents |
|---------|---------------|
| [Quickstart](https://lightning-agent.nousresearch.com/docs/getting-started/quickstart) | Install, setup, and a first conversation in 2 minutes |
| [CLI Usage](https://lightning-agent.nousresearch.com/docs/user-guide/cli) | Commands, keybindings, personalities, sessions |
| [Configuration](https://lightning-agent.nousresearch.com/docs/user-guide/configuration) | Config file, providers, models, all options |
| [Messaging Gateway](https://lightning-agent.nousresearch.com/docs/user-guide/messaging) | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Security](https://lightning-agent.nousresearch.com/docs/user-guide/security) | Command approval, DM pairing, container isolation |
| [Tools & Toolsets](https://lightning-agent.nousresearch.com/docs/user-guide/features/tools) | 40+ tools, the toolset system, terminal backends |
| [Skills System](https://lightning-agent.nousresearch.com/docs/user-guide/features/skills) | Procedural memory, Skills Hub, how to create skills |
| [Memory](https://lightning-agent.nousresearch.com/docs/user-guide/features/memory) | Persistent memory, user profiles, best practices |
| [MCP Integration](https://lightning-agent.nousresearch.com/docs/user-guide/features/mcp) | How to connect an MCP server for more capabilities |
| [Cron Scheduling](https://lightning-agent.nousresearch.com/docs/user-guide/features/cron) | Scheduled tasks with platform delivery |
| [Context Files](https://lightning-agent.nousresearch.com/docs/user-guide/features/context-files) | Project context that shapes every conversation |
| [Architecture](https://lightning-agent.nousresearch.com/docs/developer-guide/architecture) | Project structure, agent loop, key classes |
| [Contributing](https://lightning-agent.nousresearch.com/docs/developer-guide/contributing) | Development setup, PR process, code style |
| [CLI Reference](https://lightning-agent.nousresearch.com/docs/reference/cli-commands) | All commands and flags |
| [Environment Variables](https://lightning-agent.nousresearch.com/docs/reference/environment-variables) | Complete env var reference |

---

## Migrating from OpenClaw

If you come from OpenClaw, Sonic can import your settings, memories, skills, and API keys.

**During first-time setup:** The setup wizard (`sonic setup`) finds `~/.openclaw` and offers the migration before the configuration starts.

**At any time after the installation:**

```bash
sonic claw migrate              # Interactive migration (full preset)
sonic claw migrate --dry-run    # Preview what would be migrated
sonic claw migrate --preset user-data   # Migrate without secrets
sonic claw migrate --overwrite  # Overwrite existing conflicts
```

Sonic imports these items:
- **SOUL.md** — the persona file
- **Memories** — MEMORY.md and USER.md entries
- **Skills** — user-created skills, into `~/.sonic/skills/openclaw-imports/`
- **Command allowlist** — approval patterns
- **Messaging settings** — platform configs, allowed users, working directory
- **API keys** — allowlisted secrets (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **TTS assets** — workspace audio files
- **Workspace instructions** — AGENTS.md (with `--workspace-target`)

For all options, run `sonic claw migrate --help`. For an interactive migration with dry-run previews, use the `openclaw-migration` skill.

---

## Contributing

Contributions are welcome. For development setup, code style, and the PR process, read the [Contributing Guide](https://lightning-agent.nousresearch.com/docs/developer-guide/contributing).

To start as a contributor, clone the repository and run `setup-sonic.sh`:

```bash
git clone https://github.com/dabit3/sonic-agent.git
cd sonic-agent
./setup-sonic.sh     # installs uv, creates venv, installs .[all], symlinks ~/.local/bin/sonic
./sonic              # auto-detects the venv, no need to `source` first
```

The manual path does the same work:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Community

- [Discord](https://discord.gg/NousResearch)
- [Skills Hub](https://agentskills.io)
- [Issues](https://github.com/dabit3/sonic-agent/issues)
- [computer-use-linux](https://github.com/avifenesh/computer-use-linux) — a Linux desktop-control MCP server for Sonic and other MCP hosts. It gives AT-SPI accessibility trees, Wayland and X11 input, screenshots, and compositor window targeting.
- [SonicClaw](https://github.com/AaronWong1999/sonicclaw) — a community WeChat bridge. It runs Sonic Agent and OpenClaw on the same WeChat account.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [Nous Research](https://nousresearch.com).
