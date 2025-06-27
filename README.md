# Simple Minecraft Launcher

This project provides a minimal launcher for Minecraft written in Python. It can check a GitHub repository for the latest release of the game and download it if an update is available.

## Features
- Checks a GitHub repository for the most recent release.
- Downloads the release's `zipball_url` as a zip archive and extracts it into an `EPTA Client` folder.
- Supports launching the game with an offline username.
- Basic Tkinter interface to update and launch the game.
- Lets you choose where the game files are installed.
- Stores the username, game directory and installed version in `AppData/EPTAData` (or `~/.config/EPTAData`).
- Allows setting a custom base Java command in the config and appending extra
  launch arguments through the UI.
- Uses a temporary argument file when launching so the Java command stays short
  and does not hit the Windows command length limit.

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
   Press **Check for Update** to download the release via `zipball_url` and extract it.
   Afterwards press **Launch** to start the game.
   You can customise the Java command used to start the game by editing
   `config.json` inside `AppData/EPTAData` (or `~/.config/EPTAData`) and
   changing the `base_cmd_template` value. Arguments typed in the **Additional
   Launch Arguments** field will be appended to this command when launching.
   The launcher writes all JVM options to a temporary `args.txt` file before
   starting Java so the command line stays short on Windows.
   The launcher will check for Java 17+ when launching the game and offer to open a JDK download page if it is missing or outdated.


## Microsoft Login
The launcher contains only offline launching capabilities. Implementing Microsoft (Mojang) authentication requires access to Microsoft's login services, which may not be reachable in this environment.

## Building an executable

To distribute the launcher as a standalone Windows application, you can build an
`.exe` using [PyInstaller](https://pyinstaller.org/):

1. Install the dependencies and PyInstaller:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```
2. Run PyInstaller from the project directory:
   ```bash
   pyinstaller --onefile --add-data background.png:. -i epta_icon_64x64.ico --hide-console minimize-late -n EPTALauncher launcher.py
   ```
   On Linux or macOS replace the semicolon (`;`) after the image name with a
   colon (`:`).
3. The compiled launcher will be located in the `dist` folder as
   `launcher.exe` (or just `launcher` on non‑Windows platforms).
