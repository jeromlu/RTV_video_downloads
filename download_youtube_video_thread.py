# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 10:07:35 2018

@author: jeromlu2
"""

import sys
import os
import subprocess

from PyQt5.QtWidgets import QApplication, QMessageBox

from PyQt5.QtCore import QThread, pyqtSignal


class DownloadYoutubeThread(QThread):

    yt_progress = pyqtSignal(int)  # Here int to represent percentage of video
    preparation_started = pyqtSignal(str)
    start_video_loading = pyqtSignal(str)
    video_downloaded = pyqtSignal(str)
    stopped_downloading = pyqtSignal()
    converted_to_mp3 = pyqtSignal(str)

    def __init__(self, yt, stream, save_dir, to_mp3=False, parent=None):
        super(DownloadYoutubeThread, self).__init__(parent)
        self.stream = stream
        self.yt = yt
        self.file_size = stream.filesize
        # print(save_dir)
        self.save_directory = save_dir
        self.convert_mp3 = to_mp3

    def run(self):
        try:
            self.preparation_started.emit("Download started....")
            e, msg = self.download_yt_video(self.stream)
            self.video_downloaded.emit(msg)
            self.stopped_downloading.emit()
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            err_msg = "{0}:\n{1}\nError occurred in file: {2}".format(
                exc_type, exc_obj, fname
            )
            print(err_msg)
            QMessageBox.critical(self, "Error - see below", err_msg)

    def __del__(self):
        # print('stopped')
        # self.stopped_downloading.emit()
        self.wait()

    def download_yt_video(self, stream):

        try:
            video_title = self.yt.title
            file_size_MB = self.file_size / (2 ** 20)
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
            msg = 'Successfully downloaded the video "{0}" which is located at "{1}"\n\n'.format(
                video_title, self.save_directory
            )
            return True, msg
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            err_msg = "{0}:\n{1}\nError occurred in file: {2}".format(
                exc_type, exc_obj, fname
            )

            print(err_msg)
            QMessageBox.critical(self, "Error - see below", err_msg)

    def convert_to_mp3(self):
        pass


"""
import os
import subprocess

import pytube

yt = pytube.YouTube("https://www.youtube.com/watch?v=WH7xsW5Os10")

vids= yt.streams.all()
for i in range(len(vids)):
    print(i,'. ',vids[i])

vnum = int(input("Enter vid num: "))

parent_dir = r"C:\YTDownloads"
vids[vnum].download(parent_dir)

new_filename = input("Enter filename (including extension): "))  # e.g. new_filename.mp3

default_filename = vids[vnum].default_filename  # get default name using pytube API
subprocess.call(['ffmpeg', '-i',                # or subprocess.run (Python 3.5+)
    os.path.join(parent_dir, default_filename),
    os.path.join(parent_dir, new_filename)
])

print('done')
"""
