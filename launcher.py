import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import os
import subprocess
import json
import zipfile

GITHUB_REPO = "example_owner/example_repo"

# Location of the configuration file inside AppData (Windows) or ~/.config (Linux/Mac)
if os.name == "nt":
    APPDATA_DIR = os.getenv("APPDATA", os.path.expanduser("~"))
else:
    APPDATA_DIR = os.path.join(os.path.expanduser("~"), ".config")

CONFIG_DIR = os.path.join(APPDATA_DIR, "EPTAData")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_GAME_DIR_NAME = "EPTA Client"
GAME_DIR = os.path.join(os.getcwd(), DEFAULT_GAME_DIR_NAME)

USERNAME = ""
LAST_VERSION = None


def load_config():
    """Load launcher configuration from CONFIG_FILE."""
    global GAME_DIR, USERNAME, LAST_VERSION
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                GAME_DIR = data.get("game_dir", GAME_DIR)
                USERNAME = data.get("username", "")
                LAST_VERSION = data.get("last_version")
        except json.JSONDecodeError:
            pass


def save_config(game_dir, username, version):
    """Save launcher configuration to CONFIG_FILE."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"game_dir": game_dir, "username": username, "last_version": version}, f)

RELEASE_ASSET_NAME = "game.zip"


def get_latest_release_info():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None


def download_asset(asset_url, dest_path):
    response = requests.get(asset_url, timeout=10, stream=True)
    if response.status_code == 200:
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False


def check_for_update():
    """Check GitHub for a new release and install it if available."""
    global LAST_VERSION
    info = get_latest_release_info()
    if not info:
        return False, "Failed to fetch release info"

    latest_version = info.get("tag_name") or info.get("name")
    if latest_version != LAST_VERSION:
        asset = next(
            (a for a in info.get("assets", []) if a.get("name", "").endswith(".zip")),
            None,
        )
        if not asset:
            return False, "Release asset not found"

        os.makedirs(GAME_DIR, exist_ok=True)
        asset_path = os.path.join(GAME_DIR, asset.get("name"))
        if download_asset(asset.get("browser_download_url"), asset_path):
            try:
                with zipfile.ZipFile(asset_path, "r") as zip_ref:
                    zip_ref.extractall(GAME_DIR)
            except zipfile.BadZipFile:
                return False, "Downloaded file is not a valid zip archive"
            os.remove(asset_path)
            LAST_VERSION = latest_version
            save_config(GAME_DIR, USERNAME, LAST_VERSION)
            return True, f"Updated to {latest_version}"
        return False, "Failed to download asset"
    return False, "Already up to date"


def launch_game(username):
    """Launch the game using the installed JDK."""
    jar_path = os.path.join(
        GAME_DIR,
        "versions",
        "Forge 1.20.1",
        "Forge 1.20.1.jar",
    )
    if not os.path.exists(jar_path):
        messagebox.showerror("Error", "Game not found. Update first.")
        return
    cmd = ["java", "-jar", jar_path, "--username", username]
    subprocess.Popen(cmd)


class LauncherWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simple Minecraft Launcher")
        self.geometry("400x200")

        tk.Label(self, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.insert(0, USERNAME)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Game Directory:").pack(pady=5)
        self.game_dir_var = tk.StringVar(value=GAME_DIR)
        dir_frame = tk.Frame(self)
        tk.Entry(dir_frame, textvariable=self.game_dir_var, width=30).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(dir_frame, text="Browse", command=self.browse_dir).pack(side=tk.LEFT)
        dir_frame.pack(pady=5)

        update_btn = tk.Button(self, text="Check for Update", command=self.update_game)
        update_btn.pack(pady=5)

        launch_btn = tk.Button(self, text="Launch", command=self.launch)
        launch_btn.pack(pady=5)

    def browse_dir(self):
        path = filedialog.askdirectory(initialdir=self.game_dir_var.get())
        if path:
            self.game_dir_var.set(path)

    def update_game(self):
        global GAME_DIR, USERNAME
        GAME_DIR = self.game_dir_var.get().strip() or GAME_DIR
        USERNAME = self.username_entry.get().strip()
        save_config(GAME_DIR, USERNAME, LAST_VERSION)
        updated, message = check_for_update()
        messagebox.showinfo("Update", message)

    def launch(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username required")
            return
        global GAME_DIR, USERNAME
        GAME_DIR = self.game_dir_var.get().strip() or GAME_DIR
        USERNAME = username
        save_config(GAME_DIR, USERNAME, LAST_VERSION)
        launch_game(username)


def main():
    load_config()
    app = LauncherWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
