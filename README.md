# Simple Minecraft Launcher

This project provides a minimal launcher for Minecraft written in Python. It can check a GitHub repository for the latest release of the game and download it if an update is available.

## Features
- Checks a GitHub repository for the most recent release.
- Downloads the release as a zip archive and extracts it into an `EPTA Client` folder.
- Supports launching the game with an offline username.
- Basic Tkinter interface to update and launch the game.
- Lets you choose where the game files are installed.
- Stores the username, game directory and installed version in `AppData/EPTAData` (or `~/.config/EPTAData`).

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
4. Enter a username and select a folder where the game should be installed.
   Press **Check for Update** to download the latest release zip and extract it.
   Afterwards press **Launch** to start the game.

## Microsoft Login
The launcher contains only offline launching capabilities. Implementing Microsoft (Mojang) authentication requires access to Microsoft's login services, which may not be reachable in this environment.
