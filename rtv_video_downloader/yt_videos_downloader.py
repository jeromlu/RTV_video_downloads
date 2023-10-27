# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 10:07:35 2018

@author: jeromlu2
"""

import sys
import os
import pathlib
import subprocess
from typing import Optional

from PyQt6.QtWidgets import QMessageBox, QWidget

from PyQt6.QtCore import pyqtSignal, QObject

from pytube import YouTube, Stream


class DownloadYoutubeWorker(QObject):

    yt_progress = pyqtSignal(int)  # Here int to represent percentage of video
    preparation_started = pyqtSignal(str)
    start_video_loading = pyqtSignal(str)
    video_downloaded = pyqtSignal(str)
    converted_to_mp3 = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(
        self,
        yt: YouTube,
        stream: Stream,
        save_dir: pathlib.Path,
        to_mp3: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super(DownloadYoutubeWorker, self).__init__(parent)
        self.stream = stream
        self.yt = yt
        self.file_size = stream.filesize
        self.save_directory = save_dir
        self.convert_mp3 = to_mp3

    def run(self):
        try:
            self.preparation_started.emit("Download started....")
            e, msg = self.download_yt_video(self.stream)
            self.video_downloaded.emit(msg)
            self.finished.emit()
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            err_msg = "{0}:\n{1}\nError occurred in file: {2}".format(exc_type, exc_obj, fname)
            print(err_msg)
            QMessageBox.critical(self.parent, "Error - see below", err_msg)

    def download_yt_video(self, stream):

        try:
            video_title = self.yt.title
            file_size_MB = self.file_size / (2**20)
            msg = "Started loading file {0} with size: {1:.2f} MB.....".format(
                video_title, file_size_MB
            )
            self.start_video_loading.emit(msg)
            stream.download(self.save_directory)
            if self.convert_mp3:
                command = r'ffmpeg -i "{0}/{1}" -f mp3 "{0}/{2}.mp3"'
                command = command.format(
                    self.save_directory, stream.default_filename, video_title
                )
                # print(command)
                subprocess.call(command)
                self.converted_to_mp3.emit(
                    "Video additionally converted to mp3: " + video_title + ".mp3"
                )
            msg = (
                'Successfully downloaded the video "{0}" which is located at "{1}"\n\n'.format(
                    video_title, self.save_directory
                )
            )
            return True, msg
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            err_msg = "{0}:\n{1}\nError occurred in file: {2}".format(exc_type, exc_obj, fname)

            print(err_msg)
            QMessageBox.critical(self, "Error - see below", err_msg)

    def convert_to_mp3(self):
        # TODO currently I am using ffmpeg.
        pass
