from PyQt5 import QtWidgets, QtCore, QtGui
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
import shlex
import re
import requests
import ctypes
from ctypes import wintypes


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

# GitHub repo for updates (launcher itself)
LAUNCHER_VERSION = "v1.4"
LAUNCHER_REPO = "samebr0dy/LauncherEPTA"

# Base URL for client updates
BUCKET_URL = "https://storage.yandexcloud.net/eptaclient"

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
EXTRA_ARGS = ""
RAM_MB = 8192
AUTO_UPDATE = False

# Placeholder for JVM arguments. Keeping it on one short line avoids super long source lines.
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
    global GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS, RAM_MB, AUTO_UPDATE
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                GAME_DIR = data.get("game_dir", GAME_DIR)
                USERNAME = data.get("username", "")
                LAST_VERSION = data.get("last_version")
                EXTRA_ARGS = data.get("extra_args", "")
                RAM_MB = data.get("ram_mb", RAM_MB)
                AUTO_UPDATE = data.get("auto_update", AUTO_UPDATE)
        except json.JSONDecodeError:
            pass


def save_config(game_dir: str, username: str, version: str | None, extra_args: str, ram_mb: int, auto_update: bool):
    """Save launcher configuration to CONFIG_FILE."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "game_dir": game_dir,
            "username": username,
            "last_version": version,
            "extra_args": extra_args,
            "ram_mb": ram_mb,
            "auto_update": auto_update,
        }, f)


def get_latest_release_info():
    """Return metadata about the latest client release from BUCKET_URL."""
    url = f"{BUCKET_URL}/last_version.json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
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


def get_json_safe(url: str):
    """Fetch JSON data from url. Return None on error."""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def get_latest_launcher_release():
    url = f"https://api.github.com/repos/{LAUNCHER_REPO}/releases/latest"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def _run_launcher_updater(zip_url: str, latest_version: str, progress_callback=None):
    if os.name != "nt":
        return False  # Batch script is Windows-specific
    exe_path = sys.executable
    base_dir = os.path.dirname(exe_path)
    zip_path = os.path.join(base_dir, f"launcher_update_{latest_version}.zip")
    if not download_asset(zip_url, zip_path, progress_callback):
        return False
    script_path = os.path.join(base_dir, "_update_launcher.bat")
    script = f"""
@echo off
:: Wait for the launcher to close
timeout /t 2 /nobreak >nul
:: Attempt to delete the old executable
for /l %%i in (1,1,30) do (
    del "{exe_path}" >nul 2>&1
    if not exist "{exe_path}" goto :extract
    timeout /t 1 /nobreak >nul
)
echo Failed to delete old executable
exit /b 1
:extract
:: Extract the zip file using PowerShell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '{zip_path}' -DestinationPath '{base_dir}' -Force"
if %ERRORLEVEL% neq 0 (
    echo Failed to extract update
    exit /b 1
)
:: Delete the zip file
del "{zip_path}" >nul 2>&1
:: Start the new launcher
start "" "{exe_path}"
:: Delete this script
del "%~f0"
    """
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    subprocess.Popen([script_path], creationflags=subprocess.CREATE_NO_WINDOW)
    return True


def check_for_launcher_update(progress_callback=None) -> bool:
    """Check GitHub for a new launcher release and apply it."""
    info = get_latest_launcher_release()
    if not info:
        return False
    latest_version = info.get("tag_name") or info.get("name")
    if latest_version == LAUNCHER_VERSION:
        return False
    asset_url = None
    for asset in info.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith(".zip"):
            asset_url = asset.get("browser_download_url")
            break
    if not asset_url:
        return False
    if _run_launcher_updater(asset_url, latest_version, progress_callback):
        print(f"Launcher updated to {latest_version}")
        return True
    return False


def check_for_update(progress_callback=None):
    """Check the bucket for a new client release and install it."""
    global LAST_VERSION

    info = get_latest_release_info()
    if not info:
        return False, "Ошибка в поиске последней версии"

    latest_version = info.get("last")
    unsupported = info.get("unsupported", [])

    jar_path = os.path.join(
        GAME_DIR, "versions", "Forge-1.20.1", "Forge-1.20.1.jar"
    )

    if LAST_VERSION is None or not os.path.exists(jar_path):
        # Full install
        base_url = f"{BUCKET_URL}/EPTAClient/eptaclientbase.zip"
        os.makedirs(GAME_DIR, exist_ok=True)
        zip_path = os.path.join(GAME_DIR, "eptaclientbase.zip")
        if not download_asset(base_url, zip_path, progress_callback):
            return False, "Ошибка при скачивании клиента"
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                members = zf.infolist()
                total = len(members) or 1
                for i, member in enumerate(members, 1):
                    zf.extract(member, GAME_DIR)
                    if progress_callback:
                        progress_callback("Распаковка", i * 100 / total)
        except zipfile.BadZipFile:
            os.remove(zip_path)
            return False, "Скачанный файл не валидный zip-архив"
        os.remove(zip_path)

        mods_info = get_json_safe(f"{BUCKET_URL}/mods/mods.json")
        if mods_info:
            mods_dir = os.path.join(GAME_DIR, "mods")
            os.makedirs(mods_dir, exist_ok=True)
            for name in mods_info.get("add") or []:
                download_asset(f"{BUCKET_URL}/mods/{name}", os.path.join(mods_dir, name), progress_callback)

        cfg_info = get_json_safe(f"{BUCKET_URL}/config/configs.json")
        if cfg_info:
            cfg_dir = os.path.join(GAME_DIR, "config")
            os.makedirs(cfg_dir, exist_ok=True)
            for name in cfg_info.get("add") or []:
                download_asset(f"{BUCKET_URL}/config/{name}", os.path.join(cfg_dir, name), progress_callback)

        kubejs_info = get_json_safe(f"{BUCKET_URL}/kubejs/kubejs.json")
        if kubejs_info:
            kubejs_dir = os.path.join(GAME_DIR, "kubejs")
            os.makedirs(kubejs_dir, exist_ok=True)
            for name in kubejs_info.get("add") or []:
                dest_path = os.path.join(kubejs_dir, name)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                download_asset(f"{BUCKET_URL}/kubejs/{name}", os.path.join(kubejs_dir, name), progress_callback)

        LAST_VERSION = latest_version
        save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS, RAM_MB, AUTO_UPDATE)
        if progress_callback:
            progress_callback("Готово", 100)
        return True, f"Установлено {latest_version}!"

    if LAST_VERSION == latest_version:
        return False, "У Вас последняя версия!"

    if LAST_VERSION in unsupported:
        return False, "Ваша версия не поддерживается, переустановите клиент"

    # Partial update
    mods_delta = get_json_safe(f"{BUCKET_URL}/{latest_version}/mods/{LAST_VERSION}.json")
    if mods_delta:
        mods_dir = os.path.join(GAME_DIR, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        for name in mods_delta.get("del") or []:
            path = os.path.join(mods_dir, name)
            if os.path.exists(path):
                os.remove(path)
        for name in mods_delta.get("add") or []:
            download_asset(f"{BUCKET_URL}/mods/{name}", os.path.join(mods_dir, name), progress_callback)

    cfg_delta = get_json_safe(f"{BUCKET_URL}/{latest_version}/configs/{LAST_VERSION}.json")
    if cfg_delta:
        cfg_dir = os.path.join(GAME_DIR, "config")
        os.makedirs(cfg_dir, exist_ok=True)
        for name in cfg_delta.get("del") or []:
            path = os.path.join(cfg_dir, name)
            if os.path.exists(path):
                os.remove(path)
        for name in cfg_delta.get("add") or []:
            download_asset(f"{BUCKET_URL}/config/{name}", os.path.join(cfg_dir, name), progress_callback)

    kubejs_delta = get_json_safe(f"{BUCKET_URL}/{latest_version}/kubejs/{LAST_VERSION}.json")
    if kubejs_delta:
        kubejs_dir = os.path.join(GAME_DIR, "kubejs")
        os.makedirs(kubejs_dir, exist_ok=True)
        for name in kubejs_delta.get("del") or []:
            path = os.path.join(kubejs_dir, name)
            if os.path.exists(path):
                os.remove(path)
        for name in kubejs_delta.get("add") or []:
            download_asset(f"{BUCKET_URL}/kubejs/{name}", os.path.join(kubejs_dir, name), progress_callback)

    LAST_VERSION = latest_version
    save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS, RAM_MB, AUTO_UPDATE)
    if progress_callback:
        progress_callback("Готово", 100)
    return True, f"Обновлено до {latest_version}!"


game_process = None
console_window = None


def start_game(show_console: bool):
    """Launch the game using DEFAULT_CMD_TEMPLATE and EXTRA_ARGS."""
    global game_process, console_window
    jar_path = os.path.join(GAME_DIR, "versions", "Forge-1.20.1", "Forge-1.20.1.jar")
    if not os.path.exists(jar_path):
        QtWidgets.QMessageBox.critical(None, "Ошибка", "Игра не найдена, сначала обновитесь")
        return
    if not check_java():
        return
    args_file = write_args_file(GAME_DIR)
    # Build command as argument list so we control quoting and can terminate the
    # actual java process later
    base = ["java", f"-Xmx{RAM_MB}M", "-Xms3031M", f"@{args_file}"]
    extra_list = shlex.split(EXTRA_ARGS) if EXTRA_ARGS else []
    cmd_list = base + extra_list + ["--username", USERNAME]
    if show_console:
        console_window = QtWidgets.QPlainTextEdit()
        console_window.setWindowTitle("Minecraft Console")
        console_window.setReadOnly(True)
        console_window.resize(800, 500)
        console_window.show()
        proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        game_process = proc
        Backend.instance.gameStateChanged.emit(True)

        def reader():
            assert proc.stdout is not None
            for line in proc.stdout:
                QtCore.QMetaObject.invokeMethod(console_window, "appendPlainText", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, line.rstrip()))
            proc.wait()
            QtCore.QMetaObject.invokeMethod(Backend.instance, "_game_finished", QtCore.Qt.QueuedConnection)

        threading.Thread(target=reader, daemon=True).start()
    else:
        game_process = subprocess.Popen(cmd_list, creationflags=subprocess.CREATE_NO_WINDOW)
        Backend.instance.gameStateChanged.emit(True)

        def waiter():
            game_process.wait()
            QtCore.QMetaObject.invokeMethod(Backend.instance, "_game_finished", QtCore.Qt.QueuedConnection)

        threading.Thread(target=waiter, daemon=True).start()

    Backend.instance.progressChanged.emit("Запуск", 100)
    QtCore.QTimer.singleShot(300, lambda: Backend.instance.progressChanged.emit("", 0))


def get_desktop_dir() -> str:
    """Return path to the user's desktop directory."""
    if os.name == "nt":
        # Query Windows for the localized Desktop folder using the shell API
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        CSIDL_DESKTOP = 0  # <desktop>
        if ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf) == 0:
            return buf.value
        return os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(os.path.expanduser("~"), "Desktop")


def create_windows_shortcut(path: str, target: str, args: str, working_dir: str, icon: str) -> None:
    """Create a .lnk shortcut using PowerShell."""
    ps_script = (
        "$WScriptShell = New-Object -ComObject WScript.Shell; "
        f"$s = $WScriptShell.CreateShortcut({json.dumps(path)}); "
        f"$s.TargetPath = {json.dumps(target)}; "
        f"$s.Arguments = {json.dumps(args)}; "
        f"$s.WorkingDirectory = {json.dumps(working_dir)}; "
    )
    if os.path.exists(icon):
        ps_script += f"$s.IconLocation = {json.dumps(icon)}; "
    ps_script += "$s.Save();"
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        check=True,
    )


def create_desktop_shortcut() -> str:
    """Create a launcher shortcut on the desktop and return the path."""
    desktop = get_desktop_dir()
    os.makedirs(desktop, exist_ok=True)

    if getattr(sys, "frozen", False):
        target_cmd = f'"{sys.executable}"'
    else:
        script = os.path.abspath(__file__)
        target_cmd = f'"{sys.executable}" "{script}"'

    if os.name == "nt":
        shortcut_path = os.path.join(desktop, "EPTA Launcher.lnk")
        icon_path = resource_path("static/img/epta_icon_64x64.ico")
        work_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else script)
        create_windows_shortcut(shortcut_path, sys.executable, script if not getattr(sys, "frozen", False) else "", work_dir, icon_path)
    else:
        shortcut_path = os.path.join(desktop, "EPTA Launcher.desktop")
        icon_path = os.path.abspath(resource_path("static/img/epta_icon_64x64.png"))
        with open(shortcut_path, "w", encoding="utf-8") as f:
            f.write("[Desktop Entry]\n")
            f.write("Version=1.0\n")
            f.write("Type=Application\n")
            f.write("Name=EPTA Launcher\n")
            f.write(f"Exec={target_cmd}\n")
            f.write(f"Path={os.path.dirname(sys.executable)}\n")
            if os.path.exists(icon_path):
                f.write(f"Icon={icon_path}\n")
            f.write("Terminal=false\n")
        os.chmod(shortcut_path, 0o755)

    return shortcut_path


class Backend(QtCore.QObject):
    instance = None
    progressChanged = QtCore.pyqtSignal(str, float)
    updateResult = QtCore.pyqtSignal(str)
    gameStateChanged = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        Backend.instance = self

    @QtCore.pyqtSlot(result='QVariantMap')
    def get_config(self):
        return {
            "game_dir": GAME_DIR,
            "username": USERNAME,
            "extra_args": EXTRA_ARGS,
            "ram_mb": RAM_MB,
            "auto_update": AUTO_UPDATE,
        }

    @QtCore.pyqtSlot(str, str, str, int, bool, bool)
    def update_game(self, game_dir: str, username: str, extra: str, ram_mb: int, auto_update: bool, quiet: bool):
        global GAME_DIR, USERNAME, EXTRA_ARGS, RAM_MB, AUTO_UPDATE
        GAME_DIR = game_dir or GAME_DIR
        USERNAME = username
        EXTRA_ARGS = extra
        RAM_MB = ram_mb
        AUTO_UPDATE = auto_update
        save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS, RAM_MB, AUTO_UPDATE)

        def run():
            updated, message = check_for_update(progress_callback=self.progressChanged.emit)
            if not quiet or updated:
                self.updateResult.emit(message)
        threading.Thread(target=run, daemon=True).start()

    @QtCore.pyqtSlot(str, str, str, bool, bool, int)
    def launch_game(self, game_dir: str, username: str, extra: str, show_console: bool, auto_update: bool, ram_mb: int):
        global GAME_DIR, USERNAME, EXTRA_ARGS, AUTO_UPDATE, RAM_MB
        GAME_DIR = game_dir or GAME_DIR
        USERNAME = username
        EXTRA_ARGS = extra or ""
        AUTO_UPDATE = auto_update
        RAM_MB = ram_mb
        save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS, RAM_MB, AUTO_UPDATE)
        self.progressChanged.emit("Запуск", 0)
        start_game(show_console)
        self.progressChanged.emit("Запуск", 100)

    @QtCore.pyqtSlot(result=str)
    def browse_dir(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(None, "Выберите директорию для игры", GAME_DIR)
        return path or ""

    @QtCore.pyqtSlot(result=str)
    def create_shortcut(self):
        try:
            path = create_desktop_shortcut()
            return f"Ярлык создан: {path}"
        except Exception as e:
            return f"Ошибка создания ярлыка: {e}"

    @QtCore.pyqtSlot()
    def close_game(self):
        if game_process:
            game_process.terminate()

    @QtCore.pyqtSlot()
    def _game_finished(self):
        global game_process, console_window
        if console_window:
            console_window.close()
            console_window = None
        game_process = None
        self.gameStateChanged.emit(False)
        self.progressChanged.emit("", 0)


class StatusWindow(QtWidgets.QWidget):
    """A simple window to show status during launcher update check."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPTA Launcher")
        self.setFixedSize(300, 100)
        layout = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel("Проверка обновлений лаунчера...")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.center()

    def center(self):
        """Center the window on the screen."""
        frame = self.frameGeometry()
        center = QtWidgets.QDesktopWidget().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())

    def set_status(self, message: str):
        """Update the status message."""
        self.label.setText(message)


class WebApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"EPTA Launcher {LAUNCHER_VERSION}")
        ico_path = resource_path("static/img/epta_icon_64x64.ico")
        if os.path.exists(ico_path):
            # Qt stylesheets choke on backslashes; use forward slashes
            qpathico = os.path.abspath(ico_path).replace("\\", "/")
            self.setWindowIcon(QtGui.QIcon(qpathico))
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
    app = QtWidgets.QApplication(sys.argv)
    status_window = StatusWindow()
    status_window.show()
    load_config()

    def check_updates():
        if check_for_launcher_update():
            QtCore.QMetaObject.invokeMethod(status_window, "set_status", 
                                            QtCore.Qt.QueuedConnection, 
                                            QtCore.Q_ARG(str, "Лаунчер обновляется..."))
            QtCore.QTimer.singleShot(1000, lambda: QtWidgets.QMessageBox.information(None, "Обновление", 
                                                                                    "Лаунчер обновляется! После проверки лаунчер откроется автоматически!"))
            QtCore.QMetaObject.invokeMethod(status_window, "close", QtCore.Qt.QueuedConnection)
            return
        QtCore.QMetaObject.invokeMethod(status_window, "set_status", 
                                        QtCore.Qt.QueuedConnection, 
                                        QtCore.Q_ARG(str, "Проверка завершена, запуск лаунчера..."))
        QtCore.QTimer.singleShot(500, status_window.close)
        window = WebApp()
        window.show()

    threading.Thread(target=check_updates, daemon=True).start()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
