---
sidebar_position: 2
title: "Installation"
description: "Install Sonic Agent on Linux, macOS, WSL2, native Windows, or Android via Termux"
---

# Installation

Get Sonic Agent up and running in under two minutes!

## Quick Install
### With the Sonic Desktop installer on macOS or Windows (recommended)
To easily install the command-line and desktop applications, [download the Sonic Desktop installer](https://github.com/dabit3/sonic-agent/releases/latest) from our website and run it.

### Without Sonic Desktop:
For a command-line only install without Sonic Desktop, run:

#### Linux / macOS / WSL2 / Android (Termux)
```bash
curl -fsSL https://raw.githubusercontent.com/dabit3/sonic-agent/main/scripts/install.sh | bash
```

#### Windows (native)

Run in powershell:
```powershell
iex (irm https://raw.githubusercontent.com/dabit3/sonic-agent/main/scripts/install.ps1)
```

If you want to install & run Sonic Desktop after a command-line only install, simply run
```bash
sonic desktop
```

### What the Installer Does

The installer handles everything automatically — all dependencies (Python, Node.js, ripgrep, ffmpeg), the repo clone, virtual environment, global `sonic` command setup, and LLM provider configuration. By the end, you're ready to chat.

#### Install Layout

Where the installer puts things depends on whether you're installing as a normal user or as root:

| Installer | Code lives at | `sonic` binary | Data directory |
|---|---|---|---|
| pip install | Python site-packages | `~/.local/bin/sonic` (console_scripts) | `~/.sonic/` |
| Per-user (git installer) | `~/.sonic/sonic-agent/` | `~/.local/bin/sonic` (symlink) | `~/.sonic/` |
| Root-mode (`sudo curl … \| sudo bash`) | `/usr/local/lib/sonic-agent/` | `/usr/local/bin/sonic` | `/root/.sonic/` (or `$SONIC_HOME`) |

The root-mode **FHS layout** (`/usr/local/lib/…`, `/usr/local/bin/sonic`) matches where other system-wide developer tools land on Linux. It's useful for shared-machine deployments where one system install should serve every user. Per-user config (auth, skills, sessions) still lives under each user's `~/.sonic/` or explicit `SONIC_HOME`.

### After Installation

Reload your shell and start chatting:

```bash
source ~/.bashrc   # or: source ~/.zshrc
sonic             # Start chatting!
```

To reconfigure individual settings later, use the dedicated commands:

```bash
sonic model          # Choose your LLM provider and model
sonic tools          # Configure which tools are enabled
sonic gateway setup  # Set up messaging platforms
sonic config set     # Set individual config values
sonic setup          # Or run the full setup wizard to configure everything at once
```

:::tip Fastest path: Nous Portal
One subscription covers 300+ models plus the [Tool Gateway](/user-guide/features/tool-gateway) (web search, image generation, TTS, cloud browser). Skip the per-tool key juggling:

```bash
sonic setup --portal
```

That logs you in, sets Nous as your provider, and turns on the Tool Gateway in one command.
:::

---

## Prerequisites

**Installer:** On non-Windows platforms, the only prerequisite is **Git**. The installer automatically handles everything else:

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

Running Sonic as a dedicated unprivileged user (e.g. a `sonic` systemd service account, or any user without `sudo` access) is supported. The only thing on the install path that genuinely needs root is Playwright's `--with-deps` step, which `apt`-installs shared libraries (`libnss3`, `libxkbcommon`, etc.) used by Chromium. The installer detects whether sudo is available and gracefully degrades when it isn't — it will install the Chromium binary into the service user's own Playwright cache and print the exact command an administrator needs to run separately.

**Recommended split (Debian/Ubuntu):**

1. **One time, as an admin user with sudo**, install the system libraries Chromium needs:
   ```bash
   sudo npx playwright install-deps chromium
   ```
   (You can run this from anywhere — `npx` will fetch Playwright on the fly.)

2. **As the unprivileged service user**, run the regular installer. It will detect the missing sudo, skip `--with-deps`, and install Chromium into the user's local Playwright cache:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/dabit3/sonic-agent/main/scripts/install.sh | bash
   ```

   If you want to skip the Playwright step entirely — for example because you're running headless and don't need browser automation — pass `--skip-browser`:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/dabit3/sonic-agent/main/scripts/install.sh | bash -s -- --skip-browser
   ```

3. **Make `sonic` available to the service user's shells.** The installer writes the launcher to `~/.local/bin/sonic`. System service accounts often have a minimal PATH that doesn't include `~/.local/bin`. Either add it to the user's environment, or symlink the launcher into a system location:
   ```bash
   # Option A — add to the service user's profile
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

   # Option B — symlink system-wide (run as an admin)
   sudo ln -s /home/sonic/.sonic/sonic-agent/venv/bin/sonic /usr/local/bin/sonic
   ```

4. **Verify:** `sonic doctor` should now run cleanly. If you get `ModuleNotFoundError: No module named 'dotenv'`, you're invoking the repo source `sonic` file (`~/.sonic/sonic-agent/sonic`) with system Python instead of the venv launcher (`~/.sonic/sonic-agent/venv/bin/sonic`) — fix step 3.

The same pattern works on Arch (the installer uses pacman with the same sudo-detection logic), Fedora/RHEL, and openSUSE — those distros don't support `--with-deps` at all, so an administrator always installs the system libraries separately. The relevant `dnf`/`zypper` commands are printed by the installer.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `sonic: command not found` | Reload your shell (`source ~/.bashrc`) or check PATH |
| `API key not set` | Run `sonic model` to configure your provider, or `sonic config set OPENROUTER_API_KEY your_key` |
| Missing config after update | Run `sonic config check` then `sonic config migrate` |

For more diagnostics, run `sonic doctor` — it will tell you exactly what's missing and how to fix it.

## Install method auto-detection

Sonic auto-detects whether it was installed via `pip`, the git installer, Homebrew, or NixOS, and `sonic update` prints the matching update command for that path. There's no env var to set — the detection is based on the install layout (Python site-packages, `~/.sonic/sonic-agent/`, Homebrew prefix, or Nix store path). `sonic doctor` also surfaces the detected method under its environment summary.
