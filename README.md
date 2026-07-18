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

**Easiest — the .deb package:** download `rikus-mintshot_*.deb` from the
[Releases](https://github.com/Zahnschmerz/rikus-mintshot/releases) page and open it
with your package installer (or run `sudo apt install ./rikus-mintshot_*.deb`).
Then start **Rikus Mintshot** from your applications menu.

**Or from source:** run `python3 rikus-mintshot.py` (or double-click it in your file
manager and choose "Run"). On first start the app checks what's missing (mainly the
`refractasnapshot` engine, which isn't in Mint's default repos) and offers to install
it — one password prompt, a few minutes.

Full step-by-step instructions: **[GUIDE.md](GUIDE.md)** (English) / **[ANLEITUNG.md](ANLEITUNG.md)** (Deutsch).

## Under the hood & credits

Built on top of proven, existing tools — this project wires them together with a friendly GUI:

- **[Refracta](https://sourceforge.net/projects/refracta/)** (refractasnapshot / refractainstaller) — the actual snapshot/ISO-building engine.
- **Debian `live-boot` / `live-config`** — the live-boot machinery.
- **[Calamares](https://calamares.io/)** — the graphical installer, with a custom clone configuration (no user/locale/keyboard pages — everything comes from your clone).

## License

GPL-3.0 — free to use, study, share and modify, forever. See [LICENSE](LICENSE).
