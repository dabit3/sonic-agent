---
sidebar_position: 2
title: "Installation"
description: "Install Lightning Agent on Linux, macOS, WSL2, native Windows (early beta), or Android via Termux"
---

# Installation

Get Lightning Agent up and running in under two minutes with the one-line installer.

## Quick Install

### One-Line Installer (Linux / macOS / WSL2)

For a git-based install that tracks `main` and gives you the latest changes immediately:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/lightning-agent/main/scripts/install.sh | bash
```

### Windows (native, PowerShell) — Early Beta

:::warning Early BETA
Native Windows support is **early beta**. It installs and works for the common paths, but hasn't been road-tested as broadly as our POSIX installers. Please [file issues](https://github.com/NousResearch/lightning-agent/issues) when you hit rough edges. For the most battle-tested setup on Windows today, use the Linux/macOS one-liner above inside **WSL2** instead.
:::

Open PowerShell and run:

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/lightning-agent/main/scripts/install.ps1)
```

The installer handles **everything**: `uv`, Python 3.11, Node.js 22, `ripgrep`, `ffmpeg`, **and a portable Git Bash** (PortableGit — a self-contained Git-for-Windows distribution that ships `bash.exe` and the full POSIX toolchain Lightning uses for shell commands; on 32-bit Windows the installer falls back to MinGit, which lacks bash and disables terminal-tool / agent-browser features).  It clones the repo under `%LOCALAPPDATA%\lightning\lightning-agent`, creates a virtualenv, and adds `lightning` to your **User PATH**.  Restart your terminal (or open a new PowerShell window) after the install so PATH picks up.

**How Git is handled:**
1. If `git` is already on your PATH, the installer uses your existing install.
2. Otherwise it downloads portable **PortableGit** (~50MB, from the official `git-for-windows` GitHub release) and unpacks it to `%LOCALAPPDATA%\lightning\git`.  No admin rights required.  Completely isolated — it won't interfere with any system Git install, broken or otherwise.  (On 32-bit Windows it falls back to MinGit because PortableGit ships only 64-bit and ARM64 assets; bash-dependent Lightning features won't work on 32-bit hosts.)

**Why not use winget?**  Earlier designs auto-installed Git via `winget install Git.Git`, but winget fails badly when a system Git install is in a partial or broken state (exactly when users need the installer to just work).  The portable Git approach sidesteps winget, the Windows installer registry, and any existing system Git entirely.  If the Lightning Git install itself ever breaks, `Remove-Item %LOCALAPPDATA%\lightning\git` and re-run the installer — no system impact, no uninstall drama.

The installer also sets `LIGHTNING_GIT_BASH_PATH` to the located `bash.exe` so Lightning resolves it deterministically in fresh shells.

If you prefer WSL2, the Linux installer above works inside it; both native and WSL installs can coexist without conflict (native data lives under `%LOCALAPPDATA%\lightning`, WSL data lives under `~/.lightning`).

**Desktop installer (alternative):** A thin GUI installer is also available — download Lightning Desktop, run the `.exe`, and on first launch it calls `install.ps1` under the hood to provision Python (via `uv`), Node, PortableGit, and the rest of the dependencies. The desktop app and the PowerShell-installed CLI share the same install and data directories, so you can use either or both. See the [Windows (Native) guide](../user-guide/windows-native#desktop-installer-alternative) for details.

### Android / Termux

Lightning now ships a Termux-aware installer path too:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/lightning-agent/main/scripts/install.sh | bash
```

The installer detects Termux automatically and switches to a tested Android flow:
- uses Termux `pkg` for system dependencies (`git`, `python`, `nodejs`, `ripgrep`, `ffmpeg`, build tools)
- creates the virtualenv with `python -m venv`
- exports `ANDROID_API_LEVEL` automatically for Android wheel builds
- prefers the broad `.[termux-all]` extra and falls back to the smaller `.[termux]` extra (and finally a base install) if the first attempt fails to compile
- skips the untested browser / WhatsApp bootstrap by default

If you want the fully explicit path, follow the dedicated [Termux guide](./termux.md).

:::note Windows Feature Parity (Early Beta)

Native Windows is in **early beta**. Everything except the browser-based dashboard chat terminal runs natively on Windows:
- **CLI (`lightning chat`, `lightning setup`, `lightning gateway`, …)** — native, uses your default terminal
- **Gateway (Telegram, Discord, Slack, …)** — native, runs as a background PowerShell process
- **Cron scheduler** — native
- **Browser tool** — native (Chromium via Node.js)
- **MCP servers** — native (stdio and HTTP transports both supported)
- **Dashboard `/chat` terminal pane** — **WSL2 only** (uses a POSIX PTY; native Windows has no equivalent).  The rest of the dashboard (sessions, jobs, metrics) works natively — only the embedded PTY terminal tab is gated.

Set `LIGHTNING_DISABLE_WINDOWS_UTF8=1` in your environment if you hit an encoding-related bug and want to fall back to the legacy cp1252 stdio path (useful for bisecting).
:::

### What the Installer Does

The installer handles everything automatically — all dependencies (Python, Node.js, ripgrep, ffmpeg), the repo clone, virtual environment, global `lightning` command setup, and LLM provider configuration. By the end, you're ready to chat.

#### Install Layout

Where the installer puts things depends on whether you're installing as a normal user or as root:

| Installer | Code lives at | `lightning` binary | Data directory |
|---|---|---|---|
| pip install | Python site-packages | `~/.local/bin/lightning` (console_scripts) | `~/.lightning/` |
| Per-user (git installer) | `~/.lightning/lightning-agent/` | `~/.local/bin/lightning` (symlink) | `~/.lightning/` |
| Root-mode (`sudo curl … \| sudo bash`) | `/usr/local/lib/lightning-agent/` | `/usr/local/bin/lightning` | `/root/.lightning/` (or `$LIGHTNING_HOME`) |

The root-mode **FHS layout** (`/usr/local/lib/…`, `/usr/local/bin/lightning`) matches where other system-wide developer tools land on Linux. It's useful for shared-machine deployments where one system install should serve every user. Per-user config (auth, skills, sessions) still lives under each user's `~/.lightning/` or explicit `LIGHTNING_HOME`.

### After Installation

Reload your shell and start chatting:

```bash
source ~/.bashrc   # or: source ~/.zshrc
lightning             # Start chatting!
```

To reconfigure individual settings later, use the dedicated commands:

```bash
lightning model          # Choose your LLM provider and model
lightning tools          # Configure which tools are enabled
lightning gateway setup  # Set up messaging platforms
lightning config set     # Set individual config values
lightning setup          # Or run the full setup wizard to configure everything at once
```

:::tip Fastest path: Nous Portal
One subscription covers 300+ models plus the [Tool Gateway](/docs/user-guide/features/tool-gateway) (web search, image generation, TTS, cloud browser). Skip the per-tool key juggling:

```bash
lightning setup --portal
```

That logs you in, sets Nous as your provider, and turns on the Tool Gateway in one command.
:::

---

## Prerequisites

**pip install:** No prerequisites beyond Python 3.11+. Everything else is handled automatically.

**Git installer:** The only prerequisite is **Git**. The installer automatically handles everything else:

- **uv** (fast Python package manager)
- **Python 3.11** (via uv, no sudo needed)
- **Node.js v22** (for browser automation and WhatsApp bridge)
- **ripgrep** (fast file search)
- **ffmpeg** (audio format conversion for TTS)

:::info
You do **not** need to install Python, Node.js, ripgrep, or ffmpeg manually. The installer detects what's missing and installs it for you. Just make sure `git` is available (`git --version`).
:::

:::tip Nix users
If you use Nix (on NixOS, macOS, or Linux), there's a dedicated setup path with a Nix flake, declarative NixOS module, and optional container mode. See the **[Nix & NixOS Setup](./nix-setup.md)** guide.
:::

---

## Manual / Developer Installation

If you want to clone the repo and install from source — for contributing, running from a specific branch, or having full control over the virtual environment — see the [Development Setup](../developer-guide/contributing.md#development-setup) section in the Contributing guide.

---

## Non-Sudo / System Service User Installs

Running Lightning as a dedicated unprivileged user (e.g. a `lightning` systemd service account, or any user without `sudo` access) is supported. The only thing on the install path that genuinely needs root is Playwright's `--with-deps` step, which `apt`-installs shared libraries (`libnss3`, `libxkbcommon`, etc.) used by Chromium. The installer detects whether sudo is available and gracefully degrades when it isn't — it will install the Chromium binary into the service user's own Playwright cache and print the exact command an administrator needs to run separately.

**Recommended split (Debian/Ubuntu):**

1. **One time, as an admin user with sudo**, install the system libraries Chromium needs:
   ```bash
   sudo npx playwright install-deps chromium
   ```
   (You can run this from anywhere — `npx` will fetch Playwright on the fly.)

2. **As the unprivileged service user**, run the regular installer. It will detect the missing sudo, skip `--with-deps`, and install Chromium into the user's local Playwright cache:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/NousResearch/lightning-agent/main/scripts/install.sh | bash
   ```

   If you want to skip the Playwright step entirely — for example because you're running headless and don't need browser automation — pass `--skip-browser`:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/NousResearch/lightning-agent/main/scripts/install.sh | bash -s -- --skip-browser
   ```

3. **Make `lightning` available to the service user's shells.** The installer writes the launcher to `~/.local/bin/lightning`. System service accounts often have a minimal PATH that doesn't include `~/.local/bin`. Either add it to the user's environment, or symlink the launcher into a system location:
   ```bash
   # Option A — add to the service user's profile
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

   # Option B — symlink system-wide (run as an admin)
   sudo ln -s /home/lightning/.lightning/lightning-agent/venv/bin/lightning /usr/local/bin/lightning
   ```

4. **Verify:** `lightning doctor` should now run cleanly. If you get `ModuleNotFoundError: No module named 'dotenv'`, you're invoking the repo source `lightning` file (`~/.lightning/lightning-agent/lightning`) with system Python instead of the venv launcher (`~/.lightning/lightning-agent/venv/bin/lightning`) — fix step 3.

The same pattern works on Arch (the installer uses pacman with the same sudo-detection logic), Fedora/RHEL, and openSUSE — those distros don't support `--with-deps` at all, so an administrator always installs the system libraries separately. The relevant `dnf`/`zypper` commands are printed by the installer.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `lightning: command not found` | Reload your shell (`source ~/.bashrc`) or check PATH |
| `API key not set` | Run `lightning model` to configure your provider, or `lightning config set OPENROUTER_API_KEY your_key` |
| Missing config after update | Run `lightning config check` then `lightning config migrate` |

For more diagnostics, run `lightning doctor` — it will tell you exactly what's missing and how to fix it.

## Install method auto-detection

Lightning auto-detects whether it was installed via `pip`, the git installer, Homebrew, or NixOS, and `lightning update` prints the matching update command for that path. There's no env var to set — the detection is based on the install layout (Python site-packages, `~/.lightning/lightning-agent/`, Homebrew prefix, or Nix store path). `lightning doctor` also surfaces the detected method under its environment summary.
