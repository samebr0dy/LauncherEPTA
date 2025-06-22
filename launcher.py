import os
import json
import zipfile
import tempfile
import shutil
import threading
import subprocess
import requests

from PyQt5 import QtWidgets, QtGui, QtCore


GITHUB_REPO = "samebr0dy/EPTAClient"

# Configuration paths
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
EXTRA_ARGS = ""

# Placeholder for JVM arguments. In the original project this string contained
# many tuning options. Keeping it short here avoids huge source lines while still
# producing a valid argument file when launching.
JAVA_ARGS_TEMPLATE = ""

DEFAULT_CMD_TEMPLATE = r"java @{ARGS_FILE}"


def write_args_file(game_dir: str) -> str:
    """Write JVM arguments to a temporary file and return its path."""
    args = JAVA_ARGS_TEMPLATE.format(GAME_DIR=game_dir)
    tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8")
    tmp.write(args)
    tmp.close()
    return tmp.name


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
        json.dump(
            {
                "game_dir": game_dir,
                "username": username,
                "last_version": version,
                "extra_args": extra_args,
            },
            f,
        )


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
        QtWidgets.QMessageBox.critical(None, "Error", "Игра не найдена, сначала обновитесь")
        return
    args_file = write_args_file(GAME_DIR)
    base_cmd = DEFAULT_CMD_TEMPLATE.format(ARGS_FILE=args_file)
    cmd_string = f"{base_cmd} {EXTRA_ARGS} --username {USERNAME}".strip()
    subprocess.Popen(cmd_string, shell=True)


class OutlinedLabel(QtWidgets.QLabel):
    """Label that draws text with a white outline."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        font = self.font()
        metrics = QtGui.QFontMetricsF(font)
        path = QtGui.QPainterPath()
        path.addText(0, metrics.ascent(), font, self.text())
        painter.setPen(QtGui.QPen(QtCore.Qt.white, 2))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawPath(path)
        painter.setPen(QtGui.QPen(QtCore.Qt.white))
        painter.drawText(0, metrics.ascent(), self.text())


class LauncherWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPTA Launcher")
        self.setFixedSize(400, 300)

        bg_path = os.path.join(os.path.dirname(__file__), "background.png")
        if os.path.exists(bg_path):
            self.setStyleSheet(f"QWidget {{background-image: url({bg_path});}}")

        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(OutlinedLabel("Никнейм:"))
        self.username_entry = QtWidgets.QLineEdit()
        self.username_entry.setText(USERNAME)
        layout.addWidget(self.username_entry)

        layout.addWidget(OutlinedLabel("Расположение Minecraft:"))
        dir_layout = QtWidgets.QHBoxLayout()
        self.game_dir_var = QtWidgets.QLineEdit(GAME_DIR)
        dir_layout.addWidget(self.game_dir_var)
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_dir)
        dir_layout.addWidget(browse_btn)
        layout.addLayout(dir_layout)

        layout.addWidget(OutlinedLabel("Дополнительные параметры запуска:"))
        self.launch_cmd_var = QtWidgets.QLineEdit(EXTRA_ARGS)
        layout.addWidget(self.launch_cmd_var)

        self.update_btn = QtWidgets.QPushButton("Проверить обновления")
        self.launch_btn = QtWidgets.QPushButton("ЗАПУСТИТЬ")
        for btn in (self.update_btn, self.launch_btn, browse_btn):
            btn.setStyleSheet(
                "QPushButton {" "color: white; " "background-color: rgba(37,48,37,160); " "border-radius: 10px;" "}"
                "QPushButton:pressed { background-color: rgba(44,58,44,160); }"
            )

        self.update_btn.clicked.connect(self.update_game)
        self.launch_btn.clicked.connect(self.launch)
        layout.addWidget(self.update_btn)
        layout.addWidget(self.launch_btn)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

    def set_progress(self, stage: str, percent: float):
        def _update():
            self.progress.setValue(int(percent))
            self.progress.setFormat(f"{stage} {percent:.0f}%")

        QtCore.QTimer.singleShot(0, _update)

    def browse_dir(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory", self.game_dir_var.text())
        if path:
            self.game_dir_var.setText(path)

    def update_game(self):
        global GAME_DIR, USERNAME, EXTRA_ARGS
        GAME_DIR = self.game_dir_var.text().strip() or GAME_DIR
        USERNAME = self.username_entry.text().strip()
        EXTRA_ARGS = self.launch_cmd_var.text()
        save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS)
        threading.Thread(target=self._perform_update, daemon=True).start()

    def _perform_update(self):
        updated, message = check_for_update(progress_callback=self.set_progress)

        def finish():
            self.set_progress("", 0)
            QtWidgets.QMessageBox.information(self, "Update", message)

        QtCore.QTimer.singleShot(0, finish)

    def launch(self):
        username = self.username_entry.text().strip()
        if not username:
            QtWidgets.QMessageBox.critical(self, "Error", "Требуется никнейм")
            return
        global GAME_DIR, USERNAME, EXTRA_ARGS
        GAME_DIR = self.game_dir_var.text().strip() or GAME_DIR
        USERNAME = username
        EXTRA_ARGS = self.launch_cmd_var.text() or ""
        save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS)
        launch_game()


def main():
    load_config()
    app = QtWidgets.QApplication([])
    window = LauncherWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()

