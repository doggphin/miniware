# MiniWare, Temporary Alternative to MemoryWare

This project serves as a temporary alternative to MemoryWare while it's still in development. This includes an automatic final checking and media correction API built with Django and a SvelteKit interface.

---

## Automatic Installation

Most computers will be able to install everything using Chocolatey, a package manager for Windows. To run it, follow these steps:

- Open Powershell using "Run as Administrator".
- Run this command (on some computers, you may have to try mulitple times):
```
Set-ExecutionPolicy Bypass -Scope Process -Force; & "C:\Path\To\install-miniware.ps1"
```

## Manual Installation (in case automatic doesn't work)

Install the following. If in the installation process you are asked if you want to add something to path, CLICK YES!

- [Python 3.12.6](https://www.python.org/downloads/release/python-3126/)
- [Node.js](https://nodejs.org/en)
- [Git](https://git-scm.com/downloads)
- [Chocolatey](https://chocolatey.org/install)
- [FFmpeg](https://community.chocolatey.org/packages/ffmpeg)

Then make a copy of MiniWare on your computer by opening a terminal and running the command:
```
git clone https://github.com/doggphin/miniware.git
```

## Setup Instructions

- Run `install.bat` on Windows or `install.sh` on Linux to do install dependencies (only required once).

- Run `start.bat` on Windows or `start.sh` on Linux to start MiniWare.

## Update Instructions

- Run `update.bat` on Windows or `update.sh` on Linux.