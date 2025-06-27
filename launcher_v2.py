from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
import os
import sys
import json
import zipfile
import tempfile
import shutil
import threading
import subprocess
import re
import requests

# Helper to locate resources when packaged with PyInstaller
def resource_path(relative: str) -> str:
    """Return absolute path to resource for dev and PyInstaller."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative)

# Path to HTML UI
HTML_MAIN_PATH = resource_path(os.path.join("static", "html", "main_launcher.html"))

# GitHub repo for updates
GITHUB_REPO = "samebr0dy/EPTAClient"

# Configuration paths
if os.name == "nt":
    APPDATA_DIR = os.getenv("APPDATA", os.path.expanduser("~"))
else:
    APPDATA_DIR = os.path.join(os.path.expanduser("~"), ".config")

CONFIG_DIR = os.path.join(APPDATA_DIR, "EPTAData")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_GAME_DIR_NAME = ""
GAME_DIR = os.path.join(os.getcwd(), DEFAULT_GAME_DIR_NAME)

USERNAME = ""
LAST_VERSION = None
EXTRA_ARGS = r"-Xms3031M -Xmx8192M"

# Placeholder for JVM arguments. Keeping it on one short line avoids super long source lines.
JAVA_ARGS_TEMPLATE = r"-Djava.net.preferIPv4Stack=true -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:MaxGCPauseMillis=200 -XX:+AlwaysPreTouch -XX:+ParallelRefProcEnabled -XX:+UseG1GC -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCCountTarget=4 -XX:+UnlockDiagnosticVMOptions -XX:+G1SummarizeRSetStatsPeriodically -XX:SurvivorRatio=32 -XX:+UseStringDeduplication -Dlog4j2.formatMsgNoLookups=true -DlibraryDirectory={GAME_DIR} -Dlog4j.configurationFile={GAME_DIR}/config/log4j2.xml"

DEFAULT_CMD_TEMPLATE = r"java @{ARGS_FILE}"


def write_args_file(game_dir: str) -> str:
    """Write JVM arguments to a temporary file and return its path."""
    args = JAVA_ARGS_TEMPLATE.format(GAME_DIR=game_dir)
    tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8")
    tmp.write(args)
    tmp.close()
    return tmp.name


def check_java(min_version: int = 17) -> bool:
    """Return True if Java of at least min_version is available."""
    java_cmd = DEFAULT_CMD_TEMPLATE.split()[0]
    try:
        result = subprocess.run([java_cmd, "-version"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        result_output = ""
    else:
        result_output = (result.stdout or "") + (result.stderr or "")
    match = re.search(r'version "?(\d+)', result_output)
    if match and int(match.group(1)) >= min_version:
        return True
    QtWidgets.QMessageBox.critical(None, "Java", f"Java {min_version}+ не найдена")
    return False


def load_config():
    """Load launcher configuration from CONFIG_FILE."""
    global GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                GAME_DIR = data.get("game_dir", GAME_DIR)
                USERNAME = data.get("username", "")
                LAST_VERSION = data.get("last_version")
                EXTRA_ARGS = data.get("extra_args", "")
        except json.JSONDecodeError:
            pass


def save_config(game_dir: str, username: str, version: str | None, extra_args: str):
    """Save launcher configuration to CONFIG_FILE."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "game_dir": game_dir,
            "username": username,
            "last_version": version,
            "extra_args": extra_args,
        }, f)


def get_latest_release_info():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None


def download_asset(asset_url: str, dest_path: str, progress_callback=None) -> bool:
    response = requests.get(asset_url, timeout=10, stream=True)
    if response.status_code == 200:
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total and progress_callback:
                        percent = downloaded * 100 / total
                        progress_callback("Скачивание", percent)
        if progress_callback:
            progress_callback("Скачивание", 100)
        return True
    return False


def check_for_update(progress_callback=None):
    """Check GitHub for a new release and install it if available."""
    global LAST_VERSION
    info = get_latest_release_info()
    if not info:
        return False, "Ошибка в поиске последнего релиза"

    latest_version = info.get("tag_name") or info.get("name")
    jar_path = os.path.join(GAME_DIR, "versions", "Forge-1.20.1", "Forge-1.20.1.jar")
    if latest_version != LAST_VERSION or not os.path.exists(jar_path):
        zip_url = info.get("zipball_url")
        if not zip_url:
            return False, "zipball_url not found"

        os.makedirs(GAME_DIR, exist_ok=True)
        zip_path = os.path.join(GAME_DIR, f"{latest_version}.zip")
        if progress_callback:
            progress_callback("Скачивание", 0)
        if download_asset(zip_url, zip_path, progress_callback):
            try:
                tmp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    members = zip_ref.infolist()
                    total_members = len(members) or 1
                    for i, member in enumerate(members, 1):
                        zip_ref.extract(member, tmp_dir)
                        if progress_callback:
                            percent = i * 100 / total_members
                            progress_callback("Распаковка", percent)
                root_items = os.listdir(tmp_dir)
                if len(root_items) == 1 and os.path.isdir(os.path.join(tmp_dir, root_items[0])):
                    src_root = os.path.join(tmp_dir, root_items[0])
                else:
                    src_root = tmp_dir
                for item in os.listdir(src_root):
                    src = os.path.join(src_root, item)
                    dst = os.path.join(GAME_DIR, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.move(src, dst)
                    else:
                        if os.path.exists(dst):
                            os.remove(dst)
                        shutil.move(src, dst)
                shutil.rmtree(tmp_dir)
                if progress_callback:
                    progress_callback("Установка", 100)
            except zipfile.BadZipFile:
                os.remove(zip_path)
                return False, "Скачанный файл не валидный zip-архив"
            os.remove(zip_path)
            LAST_VERSION = latest_version
            save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS)
            if progress_callback:
                progress_callback("Готово", 100)
            return True, f"Обновлено до {latest_version}!"
        return False, "Ошибка при скачивании обновления"
    return False, "У Вас последняя версия!"


def launch_game():
    """Launch the game using DEFAULT_CMD_TEMPLATE and EXTRA_ARGS."""
    jar_path = os.path.join(GAME_DIR, "versions", "Forge-1.20.1", "Forge-1.20.1.jar")
    if not os.path.exists(jar_path):
        QtWidgets.QMessageBox.critical(None, "Ошибка", "Игра не найдена, сначала обновитесь")
        return
    if not check_java():
        return
    args_file = write_args_file(GAME_DIR)
    base_cmd = DEFAULT_CMD_TEMPLATE.format(ARGS_FILE=args_file)
    cmd_string = f"{base_cmd} {EXTRA_ARGS} --username {USERNAME}".strip()
    subprocess.Popen(cmd_string, shell=True)


class Backend(QtCore.QObject):
    progressChanged = QtCore.pyqtSignal(str, float)
    updateResult = QtCore.pyqtSignal(str)

    @QtCore.pyqtSlot(result='QVariantMap')
    def get_config(self):
        return {
            "game_dir": GAME_DIR,
            "username": USERNAME,
            "extra_args": EXTRA_ARGS,
        }

    @QtCore.pyqtSlot(str, str, str)
    def update_game(self, game_dir: str, username: str, extra: str):
        global GAME_DIR, USERNAME, EXTRA_ARGS
        GAME_DIR = game_dir or GAME_DIR
        USERNAME = username
        EXTRA_ARGS = extra
        save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS)
        def run():
            updated, message = check_for_update(progress_callback=self.progressChanged.emit)
            self.updateResult.emit(message)
        threading.Thread(target=run, daemon=True).start()

    @QtCore.pyqtSlot(str, str, str)
    def launch_game(self, game_dir: str, username: str, extra: str):
        global GAME_DIR, USERNAME, EXTRA_ARGS
        GAME_DIR = game_dir or GAME_DIR
        USERNAME = username
        EXTRA_ARGS = extra or ""
        save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS)
        launch_game()


class WebApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPTA Launcher")
        self.setFixedSize(1200, 700)
        self.browser = QWebEngineView()
        html_path = QtCore.QUrl.fromLocalFile(os.path.abspath(HTML_MAIN_PATH))
        self.browser.load(html_path)
        self.setCentralWidget(self.browser)

        self.channel = QWebChannel()
        self.backend = Backend()
        self.channel.registerObject('backend', self.backend)
        self.browser.page().setWebChannel(self.channel)


def main():
    load_config()
    app = QtWidgets.QApplication(sys.argv)
    window = WebApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
