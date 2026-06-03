---
sidebar_position: 3
title: "Updating & Uninstalling"
description: "How to update Sonic Agent to the latest version or uninstall it"
---

# Updating & Uninstalling

## Updating

### Git installs

Update to the latest version with a single command:

```bash
sonic update
```

This pulls the latest code from `main`, updates dependencies, and prompts you to configure any new options that were added since your last update.

### pip installs

PyPI releases track **tagged versions** (major and minor releases), not every commit on `main`. Check for updates and upgrade with:

```bash
sonic update --check    # see if a newer release is on PyPI
sonic update            # runs pip install --upgrade sonic-agent
```

Or manually:

```bash
pip install --upgrade sonic-agent    # or: uv pip install --upgrade sonic-agent
```

:::tip
`sonic update` automatically detects new configuration options and prompts you to add them. If you skipped that prompt, you can manually run `sonic config check` to see missing options, then `sonic config migrate` to interactively add them.
:::

### What happens during an update (git installs)

When you run `sonic update`, the following steps occur:

1. **Pairing-data snapshot** — a lightweight pre-update state snapshot is saved (covers `~/.sonic/pairing/`, Feishu comment rules, and other state files that get modified at runtime). Recoverable via the snapshot restore flow described under [Snapshots and rollback](../user-guide/checkpoints-and-rollback.md), or by extracting the most recent quick-snapshot zip Sonic wrote next to your `~/.sonic/` directory.
2. **Git pull** — pulls the latest code from the `main` branch and updates submodules
3. **Post-pull syntax validation + auto-rollback** — after the pull, Sonic compiles the eight critical files every `sonic` invocation imports at startup. If any fails to parse (e.g. an orphan merge-conflict marker, an accidentally truncated file), Sonic runs `git reset --hard <pre-pull-sha>` to roll the install back so your shell stays bootable. Re-run `sonic update` once the upstream fix lands.
4. **Dependency install** — runs `uv pip install -e ".[all]"` to pick up new or changed dependencies
5. **Config migration** — detects new config options added since your version and prompts you to set them
6. **Gateway auto-restart** — running gateways are refreshed after the update completes so the new code takes effect immediately. Service-managed gateways (systemd on Linux, launchd on macOS) are restarted through the service manager. Manual gateways are relaunched automatically when Sonic can map the running PID back to a profile.

### Updating against a non-default branch: `--branch`

By default `sonic update` tracks `origin/main`. Pass `--branch <name>` to update against a different branch — useful for QA channels, feature branches, or release-candidate testing:

```bash
sonic update --branch release-candidate
sonic update --check --branch experimental   # preview behindness only
```

If your local checkout is on a different branch, Sonic auto-stashes any uncommitted work, switches HEAD to the target branch, and then pulls. Branches that don't exist locally are auto-tracked from `origin/<name>` (`git checkout -B <name> origin/<name>`). Branches that don't exist anywhere fail cleanly — your stashed changes are restored before exit so you're never stranded in a weird state. The `main`-only fork-upstream sync logic is automatically skipped on non-`main` branches.

### Preview-only: `sonic update --check`

Want to know if an update is available before pulling? Run `sonic update --check` — for git installs it fetches and compares commits against `origin/main`; for pip installs it queries PyPI for the latest release. No files are modified, no gateway is restarted. Useful in scripts and cron jobs that gate on "is there an update".

### Full pre-update backup: `--backup`

For high-value profiles (production gateways, shared team installs) you can opt into a full pre-pull backup of `SONIC_HOME` (config, auth, sessions, skills, pairing):

```bash
sonic update --backup
```

Or make it the default for every run:

```yaml
# ~/.sonic/config.yaml
updates:
  pre_update_backup: true
```

`--backup` was the always-on behavior in earlier builds, but it was adding minutes to every update on large homes, so it's now opt-in. The lightweight pairing-data snapshot above still runs unconditionally.

### Windows: another `sonic.exe` is running

On Windows, `sonic update` will refuse to run if it detects another `sonic.exe` process holding the venv's entry-point executable open — most commonly the Sonic Desktop app's spawned backend, an open `sonic` REPL in another terminal, or a running gateway:

```
$ sonic update
✗ Another sonic.exe is running:
    PID 12345  sonic.exe

  Updating now would fail to overwrite ...\venv\Scripts\sonic.exe because
  Windows blocks REPLACE on a running executable.

  Close Sonic Desktop, exit any open `sonic` REPLs, and
  stop the gateway (`sonic gateway stop`) before retrying.
  Override with `sonic update --force` if you've already
  confirmed those processes will not write to the venv.
```

Close the listed processes and re-run. If you're sure the concurrent process won't interfere (rare — usually only useful when an antivirus shim is mis-attributed), pass `--force` to skip the check. In that case the updater will still retry the `.exe` rename with exponential backoff and, on stubborn locks, schedule the replacement for next reboot via `MoveFileEx(MOVEFILE_DELAY_UNTIL_REBOOT)` so the update can complete.

Expected output looks like:

```
$ sonic update
Updating Sonic Agent...
📥 Pulling latest code...
Already up to date.  (or: Updating abc1234..def5678)
📦 Updating dependencies...
✅ Dependencies updated
🔍 Checking for new config options...
✅ Config is up to date  (or: Found 2 new options — running migration...)
🔄 Restarting gateways...
✅ Gateway restarted
✅ Sonic Agent updated successfully!
```

### Recommended Post-Update Validation

`sonic update` handles the main update path, but a quick validation confirms everything landed cleanly:

1. `git status --short` — if the tree is unexpectedly dirty, inspect before continuing
2. `sonic doctor` — checks config, dependencies, and service health
3. `sonic --version` — confirm the version bumped as expected
4. If you use the gateway: `sonic gateway status`
5. If `doctor` reports npm audit issues: run `npm audit fix` in the flagged directory

:::warning Dirty working tree after update
If `git status --short` shows unexpected changes after `sonic update`, stop and inspect them before continuing. This usually means local modifications were reapplied on top of the updated code, or a dependency step refreshed lockfiles.
:::

### If your terminal disconnects mid-update

`sonic update` protects itself against accidental terminal loss:

- The update ignores `SIGHUP`, so closing your SSH session or terminal window no longer kills it mid-install. `pip` and `git` child processes inherit this protection, so the Python environment cannot be left half-installed by a dropped connection.
- All output is mirrored to `~/.sonic/logs/update.log` while the update runs. If your terminal disappears, reconnect and inspect the log to see whether the update finished and whether the gateway restart succeeded:

```bash
tail -f ~/.sonic/logs/update.log
```

- `Ctrl-C` (SIGINT) and system shutdown (SIGTERM) are still honored — those are deliberate cancellations, not accidents.

You no longer need to wrap `sonic update` in `screen` or `tmux` to survive a terminal drop.

### Checking your current version

```bash
sonic version
```

Compare against the latest release at the [GitHub releases page](https://github.com/dabit3/sonic-agent/releases).

### Updating from Messaging Platforms

You can also update directly from Telegram, Discord, Slack, WhatsApp, or Teams by sending:

```
/update
```

This pulls the latest code, updates dependencies, and restarts running gateways. The bot will briefly go offline during the restart (typically 5–15 seconds) and then resume.

### Manual Update

If you installed manually (not via the quick installer):

```bash
cd /path/to/sonic-agent
export VIRTUAL_ENV="$(pwd)/venv"

# Pull latest code
git pull origin main

# Reinstall (picks up new dependencies)
uv pip install -e ".[all]"

# Check for new config options
sonic config check
sonic config migrate   # Interactively add any missing options
```

### Rollback instructions

If an update introduces a problem, you can roll back to a previous version:

```bash
cd /path/to/sonic-agent

# List recent versions
git log --oneline -10

# Roll back to a specific commit
git checkout <commit-hash>
uv pip install -e ".[all]"

# Restart the gateway if running
sonic gateway restart
```

To roll back to a specific release tag (substitute your previous tag — e.g. a recent release like `v2026.5.16`, or any earlier tag from `git tag --sort=-version:refname`):

```bash
git checkout vX.Y.Z
uv pip install -e ".[all]"
```

:::warning
Rolling back may cause config incompatibilities if new options were added. Run `sonic config check` after rolling back and remove any unrecognized options from `config.yaml` if you encounter errors.
:::

### Note for Nix users

If you installed via Nix flake, updates are managed through the Nix package manager:

```bash
# Update the flake input
nix flake update sonic-agent

# Or rebuild with the latest
nix profile upgrade sonic-agent
```

Nix installations are immutable — rollback is handled by Nix's generation system:

```bash
nix profile rollback
```

See [Nix Setup](./nix-setup.md) for more details.

---

## Uninstalling

### Git installs

```bash
sonic uninstall
```

The uninstaller gives you the option to keep your configuration files (`~/.sonic/`) for a future reinstall.

### pip installs

```bash
pip uninstall sonic-agent
rm -rf ~/.sonic            # Optional — keep if you plan to reinstall
```

### Manual Uninstall

```bash
rm -f ~/.local/bin/sonic
rm -rf /path/to/sonic-agent
rm -rf ~/.sonic            # Optional — keep if you plan to reinstall
```

:::info
If you installed the gateway as a system service, stop and disable it first:
```bash
sonic gateway stop
# Linux: systemctl --user disable sonic-gateway
# macOS: launchctl remove ai.sonic.gateway
```
:::
