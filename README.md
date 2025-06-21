# Simple Minecraft Launcher

This project provides a minimal launcher for Minecraft written in Python. It can check a GitHub repository for the latest release of the game and download it if an update is available.

## Features
- Checks a GitHub repository for the most recent release.
- Downloads the specified release asset when an update is found.
- Supports launching the game with an offline username.
- Basic Tkinter interface to update and launch the game.

## Usage
1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Edit `launcher.py` and set `GITHUB_REPO` to the repository containing your release files.
3. Run the launcher:
   ```bash
   python launcher.py
   ```
4. Enter a username, press **Check for Update** to download the latest release, then press **Launch**.

## Microsoft Login
The launcher contains only offline launching capabilities. Implementing Microsoft (Mojang) authentication requires access to Microsoft's login services, which may not be reachable in this environment.
