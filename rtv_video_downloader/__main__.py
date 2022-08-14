from PyQt6.QtWidgets import QApplication

from rtv_video_downloader.video_downloader import MainWindow


def launch_app():
    import sys

    app = QApplication(sys.argv)

    form = MainWindow()
    form.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
