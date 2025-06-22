import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import os
import subprocess
import json
import zipfile
import tempfile
import shutil
import logging

logging.basicConfig(level=logging.INFO)

GITHUB_REPO = "samebr0dy/EPTAClient"

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
# Default template for launching the game. ``{jar_path}`` and ``{username}``
# will be replaced at runtime. You can customize this template in the
# configuration file.
DEFAULT_CMD_TEMPLATE = (
    r'java -Xms3031M -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:MaxGCPauseMillis=200 -XX:+AlwaysPreTouch -XX:+ParallelRefProcEnabled -XX:+UseG1GC -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:+UseStringDeduplication -XX:MaxTenuringThreshold=1 -XX:SurvivorRatio=32 -Xmx8192M -Dfile.encoding=UTF-8 -XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump -Djava.library.path={GAME_DIR}\versions\Forge 1.20.1\natives -Djna.tmpdir={GAME_DIR}\versions\Forge 1.20.1\natives -Dorg.lwjgl.system.SharedLibraryExtractPath={GAME_DIR}\versions\Forge 1.20.1\natives -Dio.netty.native.workdir={GAME_DIR}\versions\Forge 1.20.1\natives -Dminecraft.launcher.brand=java-minecraft-launcher -Dminecraft.launcher.version=1.6.84-j -cp {GAME_DIR}\libraries\cpw\mods\securejarhandler\2.1.10\securejarhandler-2.1.10.jar;{GAME_DIR}\libraries\org\ow2\asm\asm\9.7.1\asm-9.7.1.jar;{GAME_DIR}\libraries\org\ow2\asm\asm-commons\9.7.1\asm-commons-9.7.1.jar;{GAME_DIR}\libraries\org\ow2\asm\asm-tree\9.7.1\asm-tree-9.7.1.jar;{GAME_DIR}\libraries\org\ow2\asm\asm-util\9.7.1\asm-util-9.7.1.jar;{GAME_DIR}\libraries\org\ow2\asm\asm-analysis\9.7.1\asm-analysis-9.7.1.jar;{GAME_DIR}\libraries\net\minecraftforge\accesstransformers\8.0.4\accesstransformers-8.0.4.jar;{GAME_DIR}\libraries\org\antlr\antlr4-runtime\4.9.1\antlr4-runtime-4.9.1.jar;{GAME_DIR}\libraries\net\minecraftforge\eventbus\6.0.5\eventbus-6.0.5.jar;{GAME_DIR}\libraries\net\minecraftforge\forgespi\7.0.1\forgespi-7.0.1.jar;{GAME_DIR}\libraries\net\minecraftforge\coremods\5.2.4\coremods-5.2.4.jar;{GAME_DIR}\libraries\cpw\mods\modlauncher\10.0.9\modlauncher-10.0.9.jar;{GAME_DIR}\libraries\net\minecraftforge\unsafe\0.2.0\unsafe-0.2.0.jar;{GAME_DIR}\libraries\net\minecraftforge\mergetool\1.1.5\mergetool-1.1.5-api.jar;{GAME_DIR}\libraries\com\electronwill\night-config\core\3.6.4\core-3.6.4.jar;{GAME_DIR}\libraries\com\electronwill\night-config\toml\3.6.4\toml-3.6.4.jar;{GAME_DIR}\libraries\org\apache\maven\maven-artifact\3.8.5\maven-artifact-3.8.5.jar;{GAME_DIR}\libraries\net\jodah\typetools\0.6.3\typetools-0.6.3.jar;{GAME_DIR}\libraries\net\minecrell\terminalconsoleappender\1.2.0\terminalconsoleappender-1.2.0.jar;{GAME_DIR}\libraries\org\jline\jline-reader\3.12.1\jline-reader-3.12.1.jar;{GAME_DIR}\libraries\org\jline\jline-terminal\3.12.1\jline-terminal-3.12.1.jar;{GAME_DIR}\libraries\org\spongepowered\mixin\0.8.5\mixin-0.8.5.jar;{GAME_DIR}\libraries\org\openjdk\nashorn\nashorn-core\15.4\nashorn-core-15.4.jar;{GAME_DIR}\libraries\net\minecraftforge\JarJarSelector\0.3.19\JarJarSelector-0.3.19.jar;{GAME_DIR}\libraries\net\minecraftforge\JarJarMetadata\0.3.19\JarJarMetadata-0.3.19.jar;{GAME_DIR}\libraries\cpw\mods\bootstraplauncher\1.1.2\bootstraplauncher-1.1.2.jar;{GAME_DIR}\libraries\net\minecraftforge\JarJarFileSystems\0.3.19\JarJarFileSystems-0.3.19.jar;{GAME_DIR}\libraries\net\minecraftforge\fmlloader\1.20.1-47.4.1\fmlloader-1.20.1-47.4.1.jar;{GAME_DIR}\libraries\net\minecraftforge\fmlearlydisplay\1.20.1-47.4.1\fmlearlydisplay-1.20.1-47.4.1.jar;{GAME_DIR}\libraries\com\github\oshi\oshi-core\6.2.2\oshi-core-6.2.2.jar;{GAME_DIR}\libraries\com\google\code\gson\gson\2.10\gson-2.10.jar;{GAME_DIR}\libraries\com\google\guava\failureaccess\1.0.1\failureaccess-1.0.1.jar;{GAME_DIR}\libraries\com\google\guava\guava\31.1-jre\guava-31.1-jre.jar;{GAME_DIR}\libraries\com\ibm\icu\icu4j\71.1\icu4j-71.1.jar;{GAME_DIR}\libraries\com\mojang\authlib\4.0.43\authlib-4.0.43.jar;{GAME_DIR}\libraries\com\mojang\blocklist\1.0.10\blocklist-1.0.10.jar;{GAME_DIR}\libraries\com\mojang\brigadier\1.1.8\brigadier-1.1.8.jar;{GAME_DIR}\libraries\com\mojang\datafixerupper\6.0.8\datafixerupper-6.0.8.jar;{GAME_DIR}\libraries\com\mojang\logging\1.1.1\logging-1.1.1.jar;{GAME_DIR}\libraries\ru\tln4\empty\0.1\empty-0.1.jar;{GAME_DIR}\libraries\com\mojang\text2speech\1.17.9\text2speech-1.17.9.jar;{GAME_DIR}\libraries\commons-codec\commons-codec\1.15\commons-codec-1.15.jar;{GAME_DIR}\libraries\commons-io\commons-io\2.11.0\commons-io-2.11.0.jar;{GAME_DIR}\libraries\commons-logging\commons-logging\1.2\commons-logging-1.2.jar;{GAME_DIR}\libraries\io\netty\netty-buffer\4.1.82.Final\netty-buffer-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-codec\4.1.82.Final\netty-codec-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-common\4.1.82.Final\netty-common-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-handler\4.1.82.Final\netty-handler-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-resolver\4.1.82.Final\netty-resolver-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-transport-classes-epoll\4.1.82.Final\netty-transport-classes-epoll-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-transport-native-unix-common\4.1.82.Final\netty-transport-native-unix-common-4.1.82.Final.jar;{GAME_DIR}\libraries\io\netty\netty-transport\4.1.82.Final\netty-transport-4.1.82.Final.jar;{GAME_DIR}\libraries\it\unimi\dsi\fastutil\8.5.9\fastutil-8.5.9.jar;{GAME_DIR}\libraries\net\java\dev\jna\jna-platform\5.12.1\jna-platform-5.12.1.jar;{GAME_DIR}\libraries\net\java\dev\jna\jna\5.12.1\jna-5.12.1.jar;{GAME_DIR}\libraries\net\sf\jopt-simple\jopt-simple\5.0.4\jopt-simple-5.0.4.jar;{GAME_DIR}\libraries\org\apache\commons\commons-compress\1.21\commons-compress-1.21.jar;{GAME_DIR}\libraries\org\apache\commons\commons-lang3\3.12.0\commons-lang3-3.12.0.jar;{GAME_DIR}\libraries\org\apache\httpcomponents\httpclient\4.5.13\httpclient-4.5.13.jar;{GAME_DIR}\libraries\org\apache\httpcomponents\httpcore\4.4.15\httpcore-4.4.15.jar;{GAME_DIR}\libraries\org\apache\logging\log4j\log4j-api\2.19.0\log4j-api-2.19.0.jar;{GAME_DIR}\libraries\org\apache\logging\log4j\log4j-core\2.19.0\log4j-core-2.19.0.jar;{GAME_DIR}\libraries\org\apache\logging\log4j\log4j-slf4j2-impl\2.19.0\log4j-slf4j2-impl-2.19.0.jar;{GAME_DIR}\libraries\org\joml\joml\1.10.5\joml-1.10.5.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-glfw\3.3.1\lwjgl-glfw-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-glfw\3.3.1\lwjgl-glfw-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-glfw\3.3.1\lwjgl-glfw-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-glfw\3.3.1\lwjgl-glfw-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-jemalloc\3.3.1\lwjgl-jemalloc-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-jemalloc\3.3.1\lwjgl-jemalloc-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-jemalloc\3.3.1\lwjgl-jemalloc-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-jemalloc\3.3.1\lwjgl-jemalloc-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-openal\3.3.1\lwjgl-openal-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-openal\3.3.1\lwjgl-openal-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-openal\3.3.1\lwjgl-openal-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-openal\3.3.1\lwjgl-openal-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-opengl\3.3.1\lwjgl-opengl-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-opengl\3.3.1\lwjgl-opengl-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-opengl\3.3.1\lwjgl-opengl-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-opengl\3.3.1\lwjgl-opengl-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-stb\3.3.1\lwjgl-stb-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-stb\3.3.1\lwjgl-stb-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-stb\3.3.1\lwjgl-stb-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-stb\3.3.1\lwjgl-stb-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-tinyfd\3.3.1\lwjgl-tinyfd-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-tinyfd\3.3.1\lwjgl-tinyfd-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-tinyfd\3.3.1\lwjgl-tinyfd-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl-tinyfd\3.3.1\lwjgl-tinyfd-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl\3.3.1\lwjgl-3.3.1.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl\3.3.1\lwjgl-3.3.1-natives-windows.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl\3.3.1\lwjgl-3.3.1-natives-windows-arm64.jar;{GAME_DIR}\libraries\org\lwjgl\lwjgl\3.3.1\lwjgl-3.3.1-natives-windows-x86.jar;{GAME_DIR}\libraries\org\slf4j\slf4j-api\2.0.1\slf4j-api-2.0.1.jar;{GAME_DIR}\versions\Forge 1.20.1\Forge 1.20.1.jar -Djava.net.preferIPv6Addresses=system -DignoreList="bootstraplauncher","securejarhandler","asm-commons","asm-util","asm-analysis","asm-tree","asm","JarJarFileSystems","client-extra","fmlcore","javafmllanguage","lowcodelanguage","mclanguage","forge-","Forge 1.20.1.jar" -DmergeModules="jna-5.10.0.jar","jna-platform-5.10.0.jar" -DlibraryDirectory={GAME_DIR}\libraries -p {GAME_DIR}\libraries/cpw/mods/bootstraplauncher/1.1.2/bootstraplauncher-1.1.2.jar;{GAME_DIR}\libraries/cpw/mods/securejarhandler/2.1.10/securejarhandler-2.1.10.jar;{GAME_DIR}\libraries/org/ow2/asm/asm-commons/9.7.1/asm-commons-9.7.1.jar;{GAME_DIR}\libraries/org/ow2/asm/asm-util/9.7.1/asm-util-9.7.1.jar;{GAME_DIR}\libraries/org/ow2/asm/asm-analysis/9.7.1/asm-analysis-9.7.1.jar;{GAME_DIR}\libraries/org/ow2/asm/asm-tree/9.7.1/asm-tree-9.7.1.jar;{GAME_DIR}\libraries/org/ow2/asm/asm/9.7.1/asm-9.7.1.jar;{GAME_DIR}\libraries/net/minecraftforge/JarJarFileSystems/0.3.19/JarJarFileSystems-0.3.19.jar --add-modules ALL-MODULE-PATH --add-opens java.base/java.util.jar=cpw.mods.securejarhandler --add-opens java.base/java.lang.invoke=cpw.mods.securejarhandler --add-exports java.base/sun.security.util=cpw.mods.securejarhandler --add-exports jdk.naming.dns/com.sun.jndi.dns=java.naming -Xss2M cpw.mods.bootstraplauncher.BootstrapLauncher --version Forge 1.20.1 --gameDir {GAME_DIR} --assetsDir {GAME_DIR}\assets --assetIndex 5 --uuid c3a98f5351b53ff38de9d26d9504690c --accessToken c3a98f5351b53ff38de9d26d9504690c --clientId  --xuid  --userType legacy --versionType modified --width 925 --height 530 --launchTarget forgeclient --fml.forgeVersion 47.4.1 --fml.mcVersion 1.20.1 --fml.forgeGroup net.minecraftforge --fml.mcpVersion 20230612.114412'
)
BASE_CMD_TEMPLATE = DEFAULT_CMD_TEMPLATE
EXTRA_ARGS = ""


def load_config():
    """Load launcher configuration from CONFIG_FILE."""
    global GAME_DIR, USERNAME, LAST_VERSION, BASE_CMD_TEMPLATE, EXTRA_ARGS
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


def save_config(game_dir, username, version, extra_args):
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


def download_asset(asset_url, dest_path):
    response = requests.get(asset_url, timeout=10, stream=True)
    if response.status_code == 200:
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False


def get_default_launch_cmd(username):
    """Return the launch command using DEFAULT_CMD_TEMPLATE."""
    return DEFAULT_CMD_TEMPLATE.format(GAME_DIR=GAME_DIR, username=username)


def check_for_update():
    """Check GitHub for a new release and install it if available."""
    global LAST_VERSION
    info = get_latest_release_info()
    if not info:
        return False, "Failed to fetch release info"

    latest_version = info.get("tag_name") or info.get("name")
    if latest_version != LAST_VERSION:
        zip_url = info.get("zipball_url")
        if not zip_url:
            return False, "zipball_url not found"

        os.makedirs(GAME_DIR, exist_ok=True)
        zip_path = os.path.join(GAME_DIR, f"{latest_version}.zip")
        if download_asset(zip_url, zip_path):
            try:
                tmp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmp_dir)
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
            except zipfile.BadZipFile:
                os.remove(zip_path)
                return False, "Downloaded file is not a valid zip archive"
            os.remove(zip_path)
            LAST_VERSION = latest_version
            save_config(
                GAME_DIR,
                USERNAME,
                LAST_VERSION,
                EXTRA_ARGS,
            )
            return True, f"Updated to {latest_version}"
        return False, "Failed to download release"
    return False, "Already up to date"


def launch_game():
    """Launch the game using BASE_CMD_TEMPLATE and EXTRA_ARGS."""
    jar_path = os.path.join(
        GAME_DIR,
        "versions",
        "Forge 1.20.1",
        "Forge 1.20.1.jar",
    )
    if not os.path.exists(jar_path):
        messagebox.showerror("Error", "Game not found. Update first.")
        return
    base_cmd = DEFAULT_CMD_TEMPLATE.format(GAME_DIR=GAME_DIR, username=USERNAME)
    cmd_string = f"{base_cmd} {EXTRA_ARGS}".strip()
    logging.info(cmd_string)
    logging.info(subprocess.Popen(cmd_string, shell=True))


class LauncherWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EPTA Launcher")
        self.geometry("400x250")

        tk.Label(self, text="Никнейм:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.insert(0, USERNAME)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Расположение Minecraft:").pack(pady=5)
        self.game_dir_var = tk.StringVar(value=GAME_DIR)
        dir_frame = tk.Frame(self)
        tk.Entry(dir_frame, textvariable=self.game_dir_var, width=30).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(dir_frame, text="Browse", command=self.browse_dir).pack(side=tk.LEFT)
        dir_frame.pack(pady=5)

        tk.Label(self, text="Дополнительные параметры запуска:").pack(pady=5)
        self.launch_cmd_var = tk.StringVar(value=EXTRA_ARGS)
        tk.Entry(self, textvariable=self.launch_cmd_var, width=50).pack(pady=5)

        update_btn = tk.Button(self, text="Проверить обновления", command=self.update_game)
        update_btn.pack(pady=5)

        launch_btn = tk.Button(self, text="ЗАПУСТИТЬ", command=self.launch)
        launch_btn.pack(pady=5)

    def browse_dir(self):
        path = filedialog.askdirectory(initialdir=self.game_dir_var.get())
        if path:
            self.game_dir_var.set(path)

    def update_game(self):
        global GAME_DIR, USERNAME, EXTRA_ARGS
        GAME_DIR = self.game_dir_var.get().strip() or GAME_DIR
        USERNAME = self.username_entry.get().strip()
        EXTRA_ARGS = self.launch_cmd_var.get()
        save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS)
        updated, message = check_for_update()
        messagebox.showinfo("Update", message)

    def launch(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username required")
            return
        global GAME_DIR, USERNAME, EXTRA_ARGS
        GAME_DIR = self.game_dir_var.get().strip() or GAME_DIR
        USERNAME = username
        EXTRA_ARGS = self.launch_cmd_var.get() or ''
        save_config(GAME_DIR, USERNAME, LAST_VERSION, EXTRA_ARGS)
        launch_game()


def main():
    load_config()
    app = LauncherWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
