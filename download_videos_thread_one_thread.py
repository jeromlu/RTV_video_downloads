
import sys

from PyQt5.QtWidgets import QApplication

from PyQt5.QtCore import QThread


class DownloadThread(QThread):
    
    def __init__(self):
        super(DownloadThread, self).__init__(parent)
        
    def __del__(self):
        self.wait()
        
    def run(self):
        pass


if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    thread = DownloadThread()
    app.exec_()