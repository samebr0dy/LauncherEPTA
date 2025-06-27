from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from pathlib import Path
import os
import sys

HTML_MAIN_PATH = os.path.join(__file__, "static", "html", "main_launcher.html")
print(HTML_MAIN_PATH)


class Backend(QObject):
    @pyqtSlot(str)
    def from_js(self, message):
        print(f"[Python получил из JS]: {message}")


class WebApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML GUI")

        self.browser = QWebEngineView()
        # qpathhtml = Path("static\\html\\main_launcher.html").read_text(encoding="utf8")
        self.browser.load(QUrl.fromLocalFile("/static/html/main_launcher.html"))
        self.setFixedSize(1200, 700)

        self.setCentralWidget(self.browser)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebApp()
    window.show()
    sys.exit(app.exec_())
