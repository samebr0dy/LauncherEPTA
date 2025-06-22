import os
import json
import zipfile
import tempfile
import shutil
import threading
import subprocess
import re
import sys
import requests

import warnings

# Suppress PyQt SIP deprecation messages that fire when subclassing widgets
warnings.filterwarnings(
    "ignore",
    message=r".*sipPyTypeDict.*",
    category=DeprecationWarning,
)

from PyQt5 import QtWidgets, QtGui, QtCore


def resource_path(relative: str) -> str:
    """Return absolute path to resource for dev and PyInstaller."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative)

# Suppress deprecated SIP warnings from PyQt on Python 3.12+
warnings.filterwarnings(
    "ignore", message="sipPyTypeDict() is deprecated", category=DeprecationWarning
)


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
EXTRA_ARGS = r"-Xms3031M -Xmx8G"

# Placeholder for JVM arguments. In the original project this string contained
# many tuning options. Keeping it short here avoids huge source lines while still
# producing a valid argument file when launching.
JAVA_ARGS_TEMPLATE = r"-Djava.net.preferIPv4Stack=true -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:MaxGCPauseMillis=200 -XX:+AlwaysPreTouch -XX:+ParallelRefProcEnabled -XX:+UseG1GC -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:+UseStringDeduplication -XX:MaxTenuringThreshold=1 -XX:SurvivorRatio=32 -Dfile.encoding=UTF-8 -XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump -Djava.library.path={GAME_DIR}\versions\Forge-1.20.1\natives -Djna.tmpdir={GAME_DIR}\versions\Forge-1.20.1\natives -Dorg.lwjgl.system.SharedLibraryExtractPath={GAME_DIR}\versions\Forge-1.20.1\natives -Dio.netty.native.workdir={GAME_DIR}\versions\Forge-1.20.1\natives -Dminecraft.launcher.brand=java-minecraft-launcher -Dminecraft.launcher.version=1.6.84-j -cp {GAME_DIR}\libraries\cpw\mods\securejarhandler\2.1.10\securejarhandler-2.1.10.jar;{GAME_DIR}\libraries\org\ow2\asm\asm\9.7.1\asm-9.7.1.jar;{GAME_DIR}\libraries\org\ow2\asm\asm-commons\9.7.1\asm-commons-9.7.1.jar;{GAME_DIR}\libraries\org\ow2\asm\asm-tree\9.7.1\asm-tree-9.7.1.jar;{GAME_DIR}\libraries\org\ow2\asm\asm-util\9.7.1\asm-util-9.7.1.jar;{GAME_DIR}\libraries\org\ow2\asm\asm-analysis\9.7.1\asm-analysis-9.7.1.jar;{GAME_DIR}\libraries\net\minecraftforge\accesstransformers\8.0.4\accesstransformers-8.0.4.jar;{GAME_DIR}\libraries\org\antlr\antlr4-runtime\4.9.1\antlr4-runtime-4.9.1.jar;{GAME_DIR}\libraries\net\minecraftforge\eventbus\6.0.5\eventbus-6.0.5.jar;{GAME_DIR}\libraries\net\minecraftforge\forgespi\7.0.1\forgespi-7.0.1.jar;{GAME_DIR}\libraries\net\minecraftforge\coremods\5.2.4\coremods-5.2.4.jar;{GAME_DIR}\libraries\cpw\mods\modlauncher\10.0.9\modlauncher-10.0.9.jar;{GAME_DIR}\libraries\net\minecraftforge\unsafe\0.2.0\unsafe-0.2.0.jar;{GAME_DIR}\libraries\net\minecraftforge\mergetool\1.1.5\mergetool-1.1.5-api.jar;{GAME_DIR}\libraries\com\electronwill\night-config\core\3.6.4\core-3.6.4.jar;{GAME_DIR}\libraries\com\electronwill\night-config\toml\3.6.4\toml-3.6.4.jar;{GAME_DIR}\libraries\org\apache\maven\maven-artifact\3.8.5\maven-artifact-3.8.5.jar;{GAME_DIR}\libraries\net\jodah\typetools\0.6.3\typetools-0.6.3.jar;{GAME_DIR}\libraries\net\minecrell\terminalconsoleappender\1.2.0\terminalconsoleappender-1.2.0.jar;{GAME_DIR}\libraries\org\jline\jline-reader\3.12.1\jline-reader-3.12.1.jar;{GAME_DIR}\libraries\org\jline\jline-terminal\3.12.1\jline-terminal-3.12.1.jar;{GAME_DIR}\libraries\org\spongepowered\mixin\0.8.5\mixin-0.8.5.jar;{GAME_DIR}\libraries\org\openjdk\nashorn\nashorn-core\15.4\nashorn-core-15.4.jar;{GAME_DIR}\libraries\net\minecraftforge\JarJarSelector\0.3.19\JarJarSelector-0.3.19.jar;{GAME_DIR}\libraries\net\minecraftforge\JarJarMetadata\0.3.19\JarJarMetadata-0.3.19.jar;{GAME_DIR}\libraries\cpw\mods\bootstraplauncher\1.1.2\bootstraplauncher-1.1.2.jar;{GAME_DIR}\libraries\net\minecraftforge\JarJarFileSystems\0.3.19\JarJarFileSystems-0.3.19.jar;{GAME_DIR}\libraries\net\minecraftforge\fmlloader\1.20.1-47.4.1\fmlloader-1.20.1-47.4.1.jar;{GAME_DIR}\libraries\net\minecraftforge\fmlearlydisplay\1.20.1-47.4.1\fmlearlydisplay-1.20.1-47.4.1.jar;{GAME_DIR}\libraries\com\github\oshi\oshi-core\6.2.2\oshi-core-6.2.2.jar;{GAME_DIR}\libraries\com\google\code\gson\gson\2.10\gson-2.10.jar;{GAME_DIR}\libraries\com\google\guava\failureaccess\1.0.1\failureaccess-1.0.1.jar;{GAME_DIR}\libraries\com\google\guava\guava\31.1-jre\guava-31.1-jre.jar;{GAME_DIR}\libraries\com\ibm\icu\icu4j\71.1\icu4j-71.1.jar;{GAME_DIR}\libraries\com\mojang\authlib\4.0.43\authlib-4.0.43.jar;{GAME_DIR}\libraries\com\mojang\blocklist\1.0.10\blocklist-1.0.10.jar;{GAME_DIR}\libraries\com\mojang\brigadier\1.1.8\brigadier-1.1.8.jar;{GAME_DIR}\libraries\com\mojang\datafixerupper\6.0.8\datafixerupper-6.0.8.jar;{GAME_DIR}\libraries\com\mojang\logging\1.1.1\logging-1.1.1.jar;{GAME_DIR}\libraries\ru\tln4\empty\0.1\empty-0.1.jar;{GAME_DIR}\libraries\com\mojang\text2speech\1.17.9\text2speech-1.17.9.jar;{GAME_DIR}\libraries\commons-codec\commons-codec\1.15\commons-codec-1.15.jar;{GAME_DIR}\libraries\commons-io\commons-io\2.11.0\commons-io-2.11.0.jar;{GAME_DIR}\libraries\commons-logging\commons-logging\1.2\commons-logging-1.2.jar;{GAME_DIR}\libraries\io\netty\netty-buffer\4.1.82.Final\netty-buffer-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-codec\4.1.82.Final\netty-codec-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-common\4.1.82.Final\netty-common-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-handler\4.1.82.Final\netty-handler-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-resolver\4.1.82.Final\netty-resolver-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-transport-classes-epoll\4.1.82.Final\netty-transport-classes-epoll-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-transport-native-unix-common\4.1.82.Final\netty-transport-native-unix-common-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-transport\4.1.82.Final\netty-transport-4.1.82.Final.jar;{GAME_DIR}\libraries\it\unimi\dsi\fastutil\8.5.9\fastutil-8.5.9.jar;{GAME_DIR}\libraries\net\java\dev\jna\jna-platform\5.12.1\jna-platform-5.12.1.jar;{GAME_DIR}\libraries\net\java\dev\jna\jna\5.12.1\jna-5.12.1.jar;{GAME_DIR}\libraries\net\sf\jopt-simple\jopt-simple\5.0.4\jopt-simple-5.0.4.jar;{GAME_DIR}\libraries\org\apache\commons\commons-compress\1.21\commons-compress-1.21.jar;{GAME_DIR}\libraries\org\apache\commons\commons-lang3\3.12.0\commons-lang3-3.12.0.jar;{GAME_DIR}\libraries\org\apache\httpcomponents\httpclient\4.5.13\httpclient-4.5.13.jar;{GAME_DIR}\libraries\org\apache\httpcomponents\httpcore\4.4.15\httpcore-4.4.15.jar;{GAME_DIR}\libraries\org\apache\logging\log4j\log4j-api\2.19.0\log4j-api-2.19.0.jar;{GAME_DIR}\libraries\org\apache\logging\log4j\log4j-core\2.19.0\log4j-core-2.19.0.jar;{GAME_DIR}\libraries\org\apache\logging\log4j\log4j-slf4j2-impl\2.19.0\log4j-slf4j2-impl-2.19.0.jar;{GAME_DIR}\libraries\org\joml\joml\1.10.5\joml-1.10.5.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-glfw\3.3.1\lwjgl-glfw-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-glfw\3.3.1\lwjgl-glfw-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-glfw\3.3.1\lwjgl-glfw-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-glfw\3.3.1\lwjgl-glfw-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-jemalloc\3.3.1\lwjgl-jemalloc-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-jemalloc\3.3.1\lwjgl-jemalloc-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-jemalloc\3.3.1\lwjgl-jemalloc-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-jemalloc\3.3.1\lwjgl-jemalloc-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-openal\3.3.1\lwjgl-openal-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-openal\3.3.1\lwjgl-openal-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-openal\3.3.1\lwjgl-openal-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-openal\3.3.1\lwjgl-openal-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-opengl\3.3.1\lwjgl-opengl-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-opengl\3.3.1\lwjgl-opengl-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-opengl\3.3.1\lwjgl-opengl-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-opengl\3.3.1\lwjgl-opengl-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-stb\3.3.1\lwjgl-stb-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-stb\3.3.1\lwjgl-stb-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-stb\3.3.1\lwjgl-stb-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-stb\3.3.1\lwjgl-stb-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-tinyfd\3.3.1\lwjgl-tinyfd-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-tinyfd\3.3.1\lwjgl-tinyfd-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-tinyfd\3.3.1\lwjgl-tinyfd-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-tinyfd\3.3.1\lwjgl-tinyfd-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl\3.3.1\lwjgl-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl\3.3.1\lwjgl-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl\3.3.1\lwjgl-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl\3.3.1\lwjgl-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\slf4j\slf4j-api\2.0.1\slf4j-api-2.0.1.jar;{GAME_DIR}\versions\Forge-1.20.1\Forge-1.20.1.jar -Djava.net.preferIPv6Addresses=system -DignoreList=bootstraplauncher,securejarhandler,asm-commons,asm-util,asm-analysis,asm-tree,asm,JarJarFileSystems,client-extra,fmlcore,javafmllanguage,lowcodelanguage,mclanguage,forge-,Forge-1.20.1.jar -DmergeModules=jna-5.10.0.jar,jna-platform-5.10.0.jar -DlibraryDirectory={GAME_DIR}\libraries -p {GAME_DIR}\libraries/cpw/mods/bootstraplauncher/1.1.2/bootstraplauncher-1.1.2.jar;{GAME_DIR}\libraries/cpw/mods/securejarhandler/2.1.10/securejarhandler-2.1.10.jar;{GAME_DIR}\libraries/org/ow2/asm/asm-commons/9.7.1/asm-commons-9.7.1.jar;{GAME_DIR}\libraries/org/ow2/asm/asm-util/9.7.1/asm-util-9.7.1.jar;{GAME_DIR}\libraries/org/ow2/asm/asm-analysis/9.7.1/asm-analysis-9.7.1.jar;{GAME_DIR}\libraries/org/ow2/asm/asm-tree/9.7.1/asm-tree-9.7.1.jar;{GAME_DIR}\libraries/org/ow2/asm/asm/9.7.1/asm-9.7.1.jar;{GAME_DIR}\libraries/net/minecraftforge/JarJarFileSystems/0.3.19/JarJarFileSystems-0.3.19.jar --add-modules ALL-MODULE-PATH --add-opens java.base/java.util.jar=cpw.mods.securejarhandler --add-opens java.base/java.lang.invoke=cpw.mods.securejarhandler --add-exports java.base/sun.security.util=cpw.mods.securejarhandler --add-exports jdk.naming.dns/com.sun.jndi.dns=java.naming -Xss2M cpw.mods.bootstraplauncher.BootstrapLauncher --version Forge-1.20.1 --gameDir {GAME_DIR} --assetsDir {GAME_DIR}\assets --assetIndex 5 --uuid c3a98f5351b53ff38de9d26d9504690c --accessToken c3a98f5351b53ff38de9d26d9504690c --clientId  --xuid  --userType legacy --versionType modified --width 925 --height 530 --launchTarget forgeclient --fml.forgeVersion 47.4.1 --fml.mcVersion 1.20.1 --fml.forgeGroup net.minecraftforge --fml.mcpVersion 20230612.114412"

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
        result = subprocess.run(
            [java_cmd, "-version"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        result_output = ""
    else:
        result_output = (result.stdout or "") + (result.stderr or "")
    match = re.search(r'version "?(\d+)', result_output)
    if match and int(match.group(1)) >= min_version:
        return True
    reply = QtWidgets.QMessageBox.question(
        None,
        "Java",
        f"Java {min_version}+ не найдена. Открыть страницу скачивания JDK?",
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
    )
    if reply == QtWidgets.QMessageBox.Yes:
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl(
                "https://adoptium.net/temurin/releases/?version=" + str(min_version)
            )
        )
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
    if not check_java():
        return
    args_file = write_args_file(GAME_DIR)
    base_cmd = DEFAULT_CMD_TEMPLATE.format(ARGS_FILE=args_file)
    cmd_string = f"{EXTRA_ARGS} {base_cmd} --username {USERNAME}".strip()
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
        painter.setPen(QtGui.QPen(QtCore.Qt.white, 1))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawPath(path)
        painter.setPen(QtGui.QPen(QtCore.Qt.white))
        y = int(metrics.ascent())
        painter.drawText(0, y, self.text())


class LauncherWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPTA Launcher")
        ico_path = resource_path("epta_icon_64x64.ico")
        if os.path.exists(ico_path):
            # Qt stylesheets choke on backslashes; use forward slashes
            qpathico = os.path.abspath(ico_path).replace("\\", "/")
            self.setWindowIcon(QtGui.QIcon(qpathico))
        self.setFixedSize(400, 300)

        # Give the widget an object name so we can target it in the stylesheet
        self.setObjectName("launcher_window")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        bg_path = resource_path("background.png")
        if os.path.exists(bg_path):
            # Qt stylesheets choke on backslashes; use forward slashes
            qpath = os.path.abspath(bg_path).replace("\\", "/")
            self.setStyleSheet(
                "#launcher_window { "
                f"background-image: url('{qpath}'); "
                "background-position: center; "
                "background-repeat: no-repeat; "
                "}"
            )

        layout = QtWidgets.QVBoxLayout(self)

        user_group = QtWidgets.QVBoxLayout()
        user_group.setSpacing(0)
        user_group.addWidget(OutlinedLabel("Никнейм:"))
        self.username_entry = QtWidgets.QLineEdit()
        self.username_entry.setText(USERNAME)
        user_group.addWidget(self.username_entry)
        layout.addLayout(user_group)

        dir_group = QtWidgets.QVBoxLayout()
        dir_group.setSpacing(0)
        dir_group.addWidget(OutlinedLabel("Расположение Minecraft:"))
        dir_layout = QtWidgets.QHBoxLayout()
        self.game_dir_var = QtWidgets.QLineEdit(GAME_DIR)
        dir_layout.addWidget(self.game_dir_var)
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_dir)
        dir_layout.addWidget(browse_btn)
        dir_group.addLayout(dir_layout)
        layout.addLayout(dir_group)

        args_group = QtWidgets.QVBoxLayout()
        args_group.setSpacing(0)
        args_group.addWidget(OutlinedLabel("Дополнительные параметры запуска:"))
        self.launch_cmd_var = QtWidgets.QLineEdit(EXTRA_ARGS)
        args_group.addWidget(self.launch_cmd_var)
        layout.addLayout(args_group)
        layout.addStretch(1)

        btn_layout = QtWidgets.QHBoxLayout()
        self.update_btn = QtWidgets.QPushButton("Проверить обновления")
        self.launch_btn = QtWidgets.QPushButton("ЗАПУСТИТЬ")
        for btn in (self.update_btn, self.launch_btn, browse_btn):
            btn.setStyleSheet(
                "QPushButton {" "color: white; " "background-color: rgba(37,48,37,160); " "border-radius: 10px;" "}"
                "QPushButton:pressed { background-color: rgba(44,58,44,160); }"
            )

        self.update_btn.clicked.connect(self.update_game)
        self.launch_btn.clicked.connect(self.launch)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.launch_btn)
        layout.addLayout(btn_layout)

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
        QtCore.QMetaObject.invokeMethod(
            self,
            "_show_update_result",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, message),
        )

    @QtCore.pyqtSlot(str)
    def _show_update_result(self, message: str):
        self.set_progress("", 0)
        QtWidgets.QMessageBox.information(self, "Update", message)

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

