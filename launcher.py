import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import os
import subprocess
import json

GITHUB_REPO = "example_owner/example_repo"
DEFAULT_GAME_DIR = "game"
CONFIG_FILE = "config.json"
GAME_DIR = DEFAULT_GAME_DIR


def load_config():
    global GAME_DIR
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                GAME_DIR = data.get("game_dir", DEFAULT_GAME_DIR)
        except json.JSONDecodeError:
            GAME_DIR = DEFAULT_GAME_DIR


def save_config(game_dir):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"game_dir": game_dir}, f)
RELEASE_ASSET_NAME = "game.jar"


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


def version_file():
    return os.path.join(GAME_DIR, "version.txt")


def read_local_version():
    vf = version_file()
    if os.path.exists(vf):
        with open(vf, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def write_local_version(version):
    os.makedirs(GAME_DIR, exist_ok=True)
    vf = version_file()
    with open(vf, "w", encoding="utf-8") as f:
        f.write(version)


def check_for_update():
    info = get_latest_release_info()
    if not info:
        return False, "Failed to fetch release info"
    latest_version = info.get("tag_name")
    local_version = read_local_version()
    if latest_version != local_version:
        asset = next((a for a in info.get("assets", []) if a.get("name") == RELEASE_ASSET_NAME), None)
        if not asset:
            return False, "Release asset not found"
        os.makedirs(GAME_DIR, exist_ok=True)
        asset_path = os.path.join(GAME_DIR, RELEASE_ASSET_NAME)
        if download_asset(asset.get("browser_download_url"), asset_path):
            write_local_version(latest_version)
            return True, f"Updated to {latest_version}"
        return False, "Failed to download asset"
    return False, "Already up to date"


def launch_game(username):
    jar_path = os.path.join(GAME_DIR, RELEASE_ASSET_NAME)
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
        global GAME_DIR
        GAME_DIR = self.game_dir_var.get().strip() or DEFAULT_GAME_DIR
        save_config(GAME_DIR)
        updated, message = check_for_update()
        messagebox.showinfo("Update", message)

    def launch(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username required")
            return
        global GAME_DIR
        GAME_DIR = self.game_dir_var.get().strip() or DEFAULT_GAME_DIR
        save_config(GAME_DIR)
        launch_game(username)


def main():
    load_config()
    app = LauncherWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
