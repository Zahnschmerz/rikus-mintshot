# 📸 Rikus Mintshot

**A one-click, bootable clone of your running Linux Mint installation.**
It turns your running system into a bootable live ISO — something Linux Mint
has no built-in tool for.

Published by Gilbert Rikus · Free and open source (GPL-3.0) · No ads, no accounts.

*[Deutsche Version / German version: README.de.md](README.de.md)*

---

## What it does

Rikus Mintshot turns your running Linux Mint into a bootable live ISO — with one
click, plain-language progress, no terminal in sight. You choose **how much goes
in**, from a bare system to a full clone:

| Mode | What's included | Good for |
|---|---|---|
| **System only** | the bare system, no personal home | a clean base to hand on to others |
| ⭐ **System + my settings** | system **plus your settings** — desktop, apps, mail, backup profiles — but **without** the data mountain (cache, downloads, media, large local model files) | a lean system that's usable right away — **the recommended default** |
| **System + Home** | a full 1:1 clone including all your files | a complete backup / moving to new hardware |

Advanced users can fine-tune exactly which folders to leave out.

## Features

- **One click** — plain-language progress (step 1/2/3 + percentage), no terminal.
- **Write to USB** via Linux Mint's own image writer, with **built-in bit-by-bit verification** — no guessing whether the stick is good.
- **The live stick boots straight into your own account and language** — no generic placeholder user.
- **Boots with Secure Boot enabled** — the ISO carries the Microsoft-signed shim + Canonical-signed GRUB chain, so it starts on modern PCs (e.g. with a Windows dual-boot) *without* turning Secure Boot off. Works with it on or off.
- **"Install System" icon right on the live desktop** (powered by Calamares) does a full takeover: no user-creation step, no re-entering language/timezone/keyboard — it's all already yours.
- **Honest space preview before the build** — the program works out how big your clone will *really* be (instead of guessing) and warns only when it actually gets tight. No more builds dying halfway through.
- **Virtual machines can be left out with one tick** — visible right at the mode choice. They often sit on the system drive and would otherwise come along unasked; that is easily 60 GB.
- **German / English GUI**, chosen automatically from your system language.

## Requirements

| | |
|---|---|
| OS | Linux Mint 22.x (Cinnamon tested), x86_64 |
| Disk space | ~2× your installed system size, free |
| Internet | only for the one-time first-run setup |
| Secure Boot | **supported** — boots with it on *or* off, no BIOS changes needed |

## Getting started

**Easiest — the .deb package:** download `rikus-mintshot*.deb` from the
[Releases](https://github.com/Zahnschmerz/rikus-mintshot/releases) page and open it
with your package installer (or run `sudo apt install ~/Downloads/rikus-mintshot*.deb`).
Then start **Rikus Mintshot** from your applications menu.

> 🔒 **Verify the file (optional):** right-click the download folder → "Open in Terminal",
> then `sha256sum rikus-mintshot*.deb`. The number shown must match the one on the
> [Releases](https://github.com/Zahnschmerz/rikus-mintshot/releases) page — only **one**
> file needed, no second download.

**Or from source:** run `python3 rikus-mintshot.py` (or double-click it in your file
manager and choose "Run"). On first start the app checks what's missing (mainly a
base ISO-build helper that isn't in Mint's default repos) and offers to install
it — one password prompt, a few minutes.

Full step-by-step instructions: **[GUIDE.md](GUIDE.md)** (English) / **[ANLEITUNG.md](ANLEITUNG.md)** (Deutsch).
What changed in each release: **[CHANGELOG.md](CHANGELOG.md)**.

## What's inside

Rikus Mintshot is a **standalone program** — most of it is our own work:

- **Secure Boot chain** (signed shim + GRUB): the stick boots even with Secure Boot **on** — no need to disable anything in the BIOS.
- **The clone runs on foreign hardware:** Wi-Fi, LAN, the SSH host keys and the firmware boot order are all fixed up **inside the clone itself**, not tied to the original machine.
- **Persistence** on the stick (for MBR **and** GPT sticks), an **honest space preview** before the build, an **update notice**, and a **custom-configured installer** that carries over your account, language and settings **1:1** — with no new-user setup.

Like every Linux program it stands on open building blocks (among others **[Calamares](https://calamares.io/)** for the installer and Debian **live-boot/live-config** for the live boot). The very first step — collecting your running system into a base ISO — is done by a proven helper tool that is set up automatically on first start.

## Sister project

**[Rikus Zram](https://zram.rikus.info)** — set up and tune zram, swappiness and swap files with sliders instead of a terminal. Same idea, same principles: plain language, a preview before every change, a backup of every file, and it verifies afterwards that the change actually took effect.

Works on the same systems as Mintshot — with systemd and with SysVinit, on x86 and ARM. German and English.

[Website](https://zram.rikus.info) · [Source](https://github.com/Zahnschmerz/rikus-zram)

## License

GPL-3.0 — free to use, study, share and modify, forever. See [LICENSE](LICENSE).
