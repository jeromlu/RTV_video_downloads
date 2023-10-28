import sys

from PyQt6.QtWidgets import QApplication

from rtv_video_downloader.video_downloader import MainWindow
from rtv_video_downloader.video_downloader import exception_hook


def launch_app():
    app = QApplication(sys.argv)

    form = MainWindow()
    form.show()
    sys.exit(app.exec())


def main():
    sys.excepthook = exception_hook
    launch_app()


if __name__ == "__main__":
    main()
