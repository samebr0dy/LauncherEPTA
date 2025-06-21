import tkinter as tk
from tkinter import messagebox
import requests
import os
import subprocess
import json

GITHUB_REPO = "example_owner/example_repo"
GAME_DIR = "game"
VERSION_FILE = os.path.join(GAME_DIR, "version.txt")
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


def read_local_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def write_local_version(version):
    os.makedirs(GAME_DIR, exist_ok=True)
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
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
        self.geometry("300x150")

        tk.Label(self, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        update_btn = tk.Button(self, text="Check for Update", command=self.update_game)
        update_btn.pack(pady=5)

        launch_btn = tk.Button(self, text="Launch", command=self.launch)
        launch_btn.pack(pady=5)

    def update_game(self):
        updated, message = check_for_update()
        messagebox.showinfo("Update", message)

    def launch(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username required")
            return
        launch_game(username)


def main():
    app = LauncherWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
