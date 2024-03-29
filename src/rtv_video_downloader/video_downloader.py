# -*- coding: utf-8 -*-
"""
Created on Tue Jan  2 20:33:19 2018

@author: Luka
"""

import io
import time
import requests
import pathlib
import subprocess
import platform
import traceback
from typing import Optional
from pytube import YouTube, Playlist

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt6.QtWidgets import QPushButton, QLabel, QLineEdit, QCheckBox
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractScrollArea
from PyQt6.QtWidgets import QProgressBar
from PyQt6.QtWidgets import QFrame, QTextEdit, QFileDialog
from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

from PyQt6.QtGui import QIcon, QAction

from PyQt6.QtCore import QThread

from rtv_video_downloader import rtv_videos_downloader
from rtv_video_downloader import yt_videos_downloader

from rtv_video_downloader import qrc_resources  # noqa
from rtv_video_downloader import __version__

TEST_TABLE = ["174277055"]  # ['174524156','174525617','174527091','174528549','174528545']
TEST_YT_VIDEO = (
    r"https://www.youtube.com/watch?v="
    r"A12Vtv-pCIU&list=PLB0622Ce188vTD3ANxoQbtJzqHp75owak&index=173"
)

class MainWindow(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super(MainWindow, self).__init__(parent)

        # Welcome - about message.
        self.show_about_message()

        # Data structures.
        self.list_of_video_IDs: list = []
        self.log_texts: list = []
        self.streams: list = []
        self.yt: Optional[YouTube] = None
        self.yt_playlist: Optional[Playlist] = None
        self.yt_history: list = []
        self.yt_folder: pathlib.Path = pathlib.Path("./")
        self.down_vids_counter: int = 0

        # setup user interface
        self.create_main_window()
        self.create_menu_bar()

        self.btn_check.clicked.connect(self.check)
        self.btn_download.clicked.connect(self.download)
        self.btn_add_row.clicked.connect(self.add_row)
        self.btn_remove_row.clicked.connect(self.remove_row)
        self.btn_show_log.toggled.connect(self.log_frame.setVisible)
        self.tabs.currentChanged.connect(self.disable_btns)
        self.btn_open_CWD.clicked.connect(self.open_CWD)
        self.btn_cancel.clicked.connect(self.cancel)
        self.le_video_url.editingFinished.connect(self.clear_list)

    def create_main_window(self) -> None:
        """Creates main window: all buttons, layouts
        connections are kept outside this method.
        This method is called inside the init method
        """
        # TODO(lj): Move UI creation into separate class and python file.
        self.setWindowTitle("RTV and YT video downloader")
        self.setWindowIcon(QIcon(":/main_window_icon.png"))
        self.resize(800, 700)

        header = ["Video ID", "Video info"]
        self.table = QTableWidget()
        self.table.setColumnCount(len(header))
        self.table.setRowCount(len(TEST_TABLE) + 3)
        self.table.setHorizontalHeaderLabels(header)
        self.populate_table(TEST_TABLE)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table.resizeColumnsToContents()

        vbox_table = QVBoxLayout()
        vbox_table.addWidget(self.table)

        self.log_frame = QFrame()
        self.log_frame.setMaximumHeight(600)
        self.log_frame.setMinimumHeight(200)

        log_label = QLabel("Log text:")
        self.le_log_text = QTextEdit()
        self.le_log_text.setReadOnly(True)

        log_vbox = QVBoxLayout()
        log_vbox.addWidget(log_label)
        log_vbox.addWidget(self.le_log_text)
        self.log_frame.setLayout(log_vbox)
        self.btn_check = QPushButton("Check")
        self.btn_download = QPushButton("Download")
        self.btn_add_row = QPushButton("Add row")
        self.btn_remove_row = QPushButton("Remove last row")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_show_log = QPushButton("Log text")
        self.btn_show_log.setCheckable(True)
        self.btn_show_log.setChecked(True)

        self.btn_open_CWD = QPushButton("Open")
        self.cb_convert_mp3 = QCheckBox("Convert to mp3")
        self.cb_convert_mp3.setChecked(True)

        label_WD = QLabel("Current directory:")
        label_WD_lyt = QHBoxLayout()
        label_WD_lyt.addWidget(self.btn_open_CWD)
        label_WD_lyt.addWidget(label_WD)

        label_WD_lyt.addStretch(1)
        self.le_CWD = QLineEdit(str(self.yt_folder))
        self.le_CWD.setReadOnly(True)

        self.progress_bar = QProgressBar(self)
        # self.progress_bar.setGeometry(200, 80, 250, 20)

        vbox_WD = QVBoxLayout()
        vbox_WD.addLayout(label_WD_lyt)
        vbox_WD.addWidget(self.le_CWD)
        vbox_WD.addWidget(self.progress_bar)

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.btn_check)
        vbox1.addWidget(self.btn_download)
        vbox1.addWidget(self.btn_add_row)
        vbox1.addWidget(self.btn_remove_row)
        vbox1.addWidget(self.btn_cancel)
        vbox1.addSpacing(20)
        vbox1.addWidget(self.btn_show_log)
        vbox1.addStretch()

        self.rtv_download_tab = QWidget()
        self.rtv_download_tab.setLayout(vbox_table)

        label_url = QLabel("Video URL: ")
        self.le_video_url = QLineEdit(TEST_YT_VIDEO)

        hbox_le = QHBoxLayout()
        hbox_le.addWidget(label_url)
        hbox_le.addWidget(self.le_video_url)

        self.lw_streams = QListWidget()

        vbox_tube1 = QVBoxLayout()
        vbox_tube1.addLayout(hbox_le)
        vbox_tube1.addWidget(self.lw_streams)
        vbox_tube1.addWidget(self.cb_convert_mp3)

        self.youtube_download_tab = QWidget()
        self.youtube_download_tab.setLayout(vbox_tube1)
        # self.log_frame.hide()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.rtv_download_tab, "RTV_radio_downloads")
        self.tabs.addTab(self.youtube_download_tab, "Youtube_downloads")

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tabs)
        hbox1.addLayout(vbox1)

        vbox2 = QVBoxLayout()
        vbox2.addLayout(hbox1)
        vbox2.addLayout(vbox_WD)
        # vbox2.addWidget(self.progress_bar)
        vbox2.addWidget(self.log_frame)

        main_layout = QVBoxLayout()
        main_layout.addLayout(vbox2)

        self.main_window = QWidget()
        self.main_window.setLayout(main_layout)
        self.setCentralWidget(self.main_window)

    def create_menu_bar(self):
        """
        this is not needed yet
        changed my mind: for importing list of IDs
        """

        # file menu
        self.file_menu = self.menuBar().addMenu("&File")

        file_load_action = self.create_action(
            "&Load file",
            shortcut="Ctrl+L",
            slot=self.import_IDs,
            tip="Import text file with a column of IDs",
            icon="import-icon",
        )
        file_quit_action = self.create_action(
            "&Quit", shortcut="Ctrl+q", slot=self.close, tip="Close the application"
        )

        self.add_actions(self.file_menu, [file_load_action, file_quit_action])

        # Edit menu
        self.edit_menu = self.menuBar().addMenu("&Edit")

        set_filter_action = self.create_action(
            "Select &filter",
            shortcut="Ctrl+F",
            slot=self.refine_streams,
            tip="Select different filter to show streams in list",
            icon="filter-icon",
        )

        self.add_actions(self.edit_menu, [set_filter_action])

        # help menu
        self.help_menu = self.menuBar().addMenu("&Help")

        help_about_action = self.create_action(
            "&About",
            shortcut="Ctrl+Shift+A",
            slot=self.show_about_message,
            tip="Show info about the application.",
            icon="tv-icon",
        )

        self.add_actions(self.help_menu, [help_about_action])

    def show_about_message(self):
        QMessageBox.about(
            self,
            "This is the video downloader version: {0}".format(__version__),
            "Use <b>Video downloader</b> to download videos."
            "There are two options:<br>"
            '<a href="https://4d.rtvslo.si/arhiv/&sp=qs:raal">RTV SLO</a><br>'
            "or you should go to<br>"
            '<a href="https://www.youtube.com/?gl=SI&hl=sl">Youtube</a>.<br><br>'
            "Select one of two options and <b>click</b> one of above links to pop up "
            "appropriate web page from which you wish to select videos.<br><br>"
            "Have fun.",
        )

    def refine_streams(self):
        raise NotImplementedError("Set filter action. To do.")

    def populate_table(self, list):
        """
        Repopulates the table, with the items in list argument
        """
        rows = len(list)  # self.table.rowCount()
        self.table.setRowCount(rows)
        for i in range(len(list)):
            self.table.setItem(i, 0, QTableWidgetItem(list[i]))

    def add_row(self):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

    def remove_row(self):
        row_position = self.table.currentRow()
        if row_position == -1:  # ni vrstice
            row_position = self.table.rowCount() - 1
        self.table.removeRow(row_position)

    def import_IDs(self):
        path = "."
        fname, f_type = QFileDialog.getOpenFileName(
            self, "Import IDs from text file", path, "Text files (*.txt)"
        )
        if fname:
            fh = open(fname, "r")
            raw_text = fh.read()
            imported_IDs = raw_text.split("\n")
            self.populate_table(imported_IDs)

    def check(self):
        """Selects appropriate function of check button, according to
        the selected tab.
        """
        if self.tabs.currentIndex() == 0:
            self.check_IDs()
        elif self.tabs.currentIndex() == 1:
            self.get_formats()

    def download_playlist(self):
        if self.yt_playlist is None:
            QMessageBox.warning(self, "Download error", "Link is not a playlist.")
            return
        for yt in self.yt_playlist:
            print(f"{yt=}")
            print(f"{yt.title()=}")
            print(f"{yt.streams=}")
            stream = yt.streams.first()
            print(f"{stream=}")

    def get_formats(self):
        """Creates youtube video object
        acquires all possible selected formats and
        populates the QListWidget (formats_list)
        user has to select which format to download.
        """
        yt_url = self.le_video_url.text()
        self.yt = YouTube(yt_url)  # , on_progress_callback = self.progress_check
        self.streams = self.yt.streams.filter(progressive=True)
        self.populate_list_youtube()
        return True, "Youtube streams info acquired"

    def progress_check(self, stream=None, chunk=None, file_handle=None, remaining=None):
        # Gets the percentage of the file that has been downloaded.
        # percent = (100*(stream.filesize-remaining))/stream.filesize
        # self.progress_bar.setValue(percent)
        self.progress_bar.setRange(0, 0)

    def update_CWD(self):
        """
        syncs the line edit and actual CWD
        """
        self.le_CWD.setText(str(self.yt_folder))

    def browse_and_set_CWD(self):
        """
        select current working directory (CWD)
        """
        fname = QFileDialog.getExistingDirectory(
            self, "Where to save video?", str(self.yt_folder)
        )

        if fname:
            self.yt_folder = pathlib.Path(fname)
            self.update_CWD()
            return True
        else:
            return False

    def open_CWD(self):
        """opens CWD in windows explorer"""
        if platform.system() == "Windows":
            command = 'explorer "{0}"'.format(self.yt_folder)
            subprocess.run(command.replace("/", "\\"))
        else:
            command = "gnome-terminal -x cd {0}".format(self.yt_folder.as_posix())
            subprocess.run("gnome-terminal")

    def check_IDs(self):
        """
        Check which of the cells contain IDs of a videos that can be fetched,
        for each video some basic information is printed to the second column.
        if error, I still have to think what to do
        """
        rows = self.table.rowCount()
        for i in range(rows):
            item = self.table.item(i, 0)
            if item:
                video_ID_number = item.text()
                get_info_api = rtv_videos_downloader.RTV_VIDEO_DOWNLOAD_LINK.format(
                    video_ID_number
                )
                response = requests.get(get_info_api)
                if response.status_code != 200:
                    return False, "Error at acquiring the info about the video."
                response_dict = response.json()
                # info about the file name
                if "response" in response_dict:
                    file_name = response_dict["response"]["mediaFiles"][0]["filename"]
                    self.table.setItem(i, 1, QTableWidgetItem(file_name))
        self.table.resizeColumnsToContents()
        return True, "info added"

    def download(self):
        """Selects appropriate function of download button according to
        the selected tab - youtube or rtv
        """
        if self.tabs.currentIndex() == 0:
            self.download_videos_rtv()
        elif self.tabs.currentIndex() == 1:
            self.download_yt_video()

    def download_yt_video(self):
        """Downloads selected youtube video."""
        # get video from the user selection in the list widget
        if self.lw_streams.currentItem() is None:
            QMessageBox.warning(self, "Warning", "Please select a stream from the list.")
            return
        idx = self.lw_streams.currentRow()
        stream = self.streams[idx]

        # show file size and ask user if it is realy sure he wants to download
        answer = QMessageBox.question(
            self,
            "File size",
            "Are you sure you want to download video:<br><br>"
            + "<b>"
            + self.yt.title
            + "</b>"
            + "<br><br><br>With file size: <b>{0:.1f} MB</b>".format(
                stream.filesize / 2**20
            ),
        )
        if answer == QMessageBox.StandardButton.No:
            return

        # where to save folder
        OK = self.browse_and_set_CWD()
        if not OK:
            return

        # set up progress bar
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        # Create download worker and move it to new thread.
        self.download_thread = QThread()
        self.download_worker = yt_videos_downloader.DownloadYoutubeWorker(
            self.yt, stream, self.yt_folder, self.cb_convert_mp3.isChecked(), self
        )
        self.download_worker.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)

        # Reporting progress:
        self.download_worker.preparation_started.connect(self.add_to_log)
        self.download_worker.preparation_started.connect(self.progress_check)
        self.download_worker.start_video_loading.connect(self.add_to_log)
        self.download_worker.video_downloaded.connect(self.add_to_log)
        self.download_worker.finished.connect(self.done)
        self.download_worker.converted_to_mp3.connect(self.add_to_log)
        # Start the worker thread.
        self.download_thread.start()

        # start download
        self.start_downloading()
        self.down_vids_counter = self.down_vids_counter + 1

    def download_videos_rtv(self) -> None:
        """Create list of all videos. Subsequently, start the download thread
        and connect all the methods with the signals emitted inside the download thread.
        """
        rows = self.table.rowCount()
        number_of_rows = range(rows)
        self.list_of_video_IDs = []
        for i in number_of_rows:
            item = self.table.item(i, 0)
            if item:
                video_ID_number = item.text()
                self.list_of_video_IDs.append(video_ID_number)
        self.progress_bar.setMaximum(len(self.list_of_video_IDs))
        self.progress_bar.setValue(0)

        self.download_thread = QThread()
        self.download_worker = rtv_videos_downloader.DownloadVideoWorker(
            self.list_of_video_IDs, self
        )
        self.download_worker.moveToThread(self.download_thread)
        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)

        # Reporting progress:
        self.download_worker.preparation_started.connect(self.add_to_log)
        self.download_worker.start_video_loading.connect(self.add_to_log)
        self.download_worker.video_downloaded.connect(self.update_progress_bar)
        self.download_worker.start_downloading.connect(self.start_downloading)
        self.download_worker.finished.connect(self.done)
        # Start the worker thread.
        self.download_thread.start()

    def update_progress_bar(self, msg):
        """
        Update the progress bar, when downloading rtv videos
        First add to log text and then update the k and the progress bar
        """
        k = self.progress_bar.value()
        self.le_log_text.insertPlainText(
            time.strftime("%H:%M:%S") + ":  " + str(k) + "  " + msg + "\n\n"
        )
        self.log_texts.append(msg)
        k = self.progress_bar.value() + 1
        self.progress_bar.setValue(k)
        self.down_vids_counter = self.down_vids_counter + 1
        k = self.down_vids_counter

    def add_to_log(self, msg):
        """Adds message to the log file."""
        k = self.down_vids_counter  # self.progress_bar.value() + 1
        self.log_texts.append(msg)
        self.le_log_text.insertPlainText(
            time.strftime("%H:%M:%S") + ":  " + str(k) + "  " + msg + "\n"
        )

    def start_downloading(self):
        """start downloading, disable Download, Add row buttons
        Enable Cancel button
        """
        self.btn_cancel.setEnabled(True)
        self.btn_download.setEnabled(False)
        self.btn_add_row.setEnabled(False)

    def disable_btns(self):
        """Properly enable, disable buttonsaccording to the selected tab."""
        if self.tabs.currentIndex() == 1:
            self.btn_add_row.setEnabled(False)
            self.btn_remove_row.setEnabled(False)

        elif self.tabs.currentIndex() == 0:
            self.btn_add_row.setEnabled(True)
            self.btn_remove_row.setEnabled(True)

    def done(self):
        """
        Show the message that fetching videos is done.
        Disable Cancel button, enable the Download, Add row buttons and reset progress bar to 0
        """
        self.btn_cancel.setEnabled(False)
        self.btn_download.setEnabled(True)
        self.btn_add_row.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        QMessageBox.information(self, "Done!", "All desired videos downloaded!")
        self.disable_btns()
        self.download_thread = None

    def cancel(self):
        """Terminate download thread
        Enable Download button, Add row
        Disable Cancel button
        """
        self.download_thread.terminate()
        self.btn_cancel.setEnabled(False)
        self.btn_download.setEnabled(True)
        self.btn_add_row.setEnabled(True)
        self.progress_bar.setValue(0)
        self.disable_btns()
        QMessageBox.warning(
            self,
            "Terminated!",
            "You have terminated the download thread\n"
            "see log text to see additional info !",
        )

    def populate_list_youtube(self):
        self.lw_streams.clear()
        if len(self.streams) > 0:
            for stream in self.streams:
                item = QListWidgetItem(str(stream))
                self.lw_streams.addItem(item)

    def clear_list(self):
        self.lw_streams.clear()
        self.streams = []
        self.yt = None

    def closeEvent(self, event):
        folder = pathlib.Path("./data/history/")
        folder.mkdir(parents=True, exist_ok=True)
        time_string = time.strftime("%m-%d-%Y_%H-%M-%S")
        fname = "log_text_" + time_string + ".txt"
        with open(folder / fname, "w") as f:
            for text in self.log_texts:
                f.write(text + "\n")
        QApplication.quit()

    # ********************************************* HELPER FUNCTIONS
    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(
        self,
        text,
        slot=None,
        shortcut=None,
        icon=None,
        tip=None,
        checkable=False,
        signal="triggered()",
    ):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon("./icons/{}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action


def exception_hook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.
    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = "-" * 80
    logFile = "last_error.log"
    notice = (
        """An unhandled exception occurred. Please report the problem\n"""
        """using the error reporting dialog or via email to <%s>.\n"""
        """A log has been written to "%s".\n\nError information:\n"""
        % ("luka.jeromel@novartis.com", logFile)
    )
    versionInfo = __version__
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")
    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = "%s: \n%s" % (str(excType), str(excValue))
    sections = [separator, timeString, separator, errmsg, separator, tbinfo]
    msg = "\n".join(sections)
    try:
        f = open(logFile, "w")
        f.write(msg)
        f.write(versionInfo)
        f.close()
    except IOError:
        pass
    QMessageBox.critical(None, "Error", str(notice) + str(msg) + str(versionInfo))
