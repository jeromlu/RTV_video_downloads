import sys
import requests
import os
import re
import datetime
import pathlib
from typing import Optional

from PyQt6.QtWidgets import QMessageBox, QWidget

from PyQt6.QtCore import QObject, pyqtSignal


RTV_VIDEO_DOWNLOAD_LINK = (
    "http://api.rtvslo.si/ava/getRecording/{0}?client_id=82013fb3a531d5414f478747c1aca622"
)


class DownloadVideoWorker(QObject):
    # Custom signals.
    video_downloaded = pyqtSignal(str)
    start_downloading = pyqtSignal()
    start_video_loading = pyqtSignal(str)
    preparation_started = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, list_of_videos, parent: Optional[QObject] = None):
        super(DownloadVideoWorker, self).__init__(parent)
        self.file_size_tresh = 5000
        self.by_week = True
        self.home_folder = pathlib.Path("./downloads/RTV_downloads/")
        self.list_of_videos = list_of_videos
        self.save_directory = self.home_folder

    def run(self):
        try:
            self.start_downloading.emit()
            for video_ID_number in self.list_of_videos:
                self.preparation_started.emit(video_ID_number + ".....")
                e, msg = self.download_video_from_rtv_slo(video_ID_number)
                self.video_downloaded.emit(msg)
            self.finished.emit()
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            err_msg = "{0}:\n{1}\nError occurred in file: {2}".format(exc_type, exc_obj, fname)
            QMessageBox.critical(self.parent(), "Error - see below", err_msg)

    def download_video_from_rtv_slo(self, video_ID_number):
        get_info_api = RTV_VIDEO_DOWNLOAD_LINK.format(video_ID_number)
        response = requests.get(get_info_api)
        if response.status_code != 200:
            msg = "Error at acquiring the info about the video."
            return False, msg
        response_dict = response.json()
        if "error" in response_dict:
            msg = "Error - incorrect Video-ID"
            return False, msg

        # info about the file name
        file_name = response_dict["response"]["mediaFiles"][0]["filename"]

        # where the file is saved.. have to know in order to download the file
        http_streamer = response_dict["response"]["mediaFiles"][0]["streamers"]["http"]

        # check the file size, if it is too big will not be downloaded
        file_size = response_dict["response"]["mediaFiles"][0]["filesize"]
        file_size_MB = float(file_size) / 2**20

        if self.check_file_size(response_dict):
            msg = "File is larger than {0} MB.\nIt will not be downloaded".format(
                self.file_size_tresh
            )
            return False, msg
        else:
            # create informative file_name and appropriate file structure
            broadcast_date = response_dict["response"]["broadcastDate"]

            stub = response_dict["response"]["stub"]
            video_title = response_dict["response"]["title"]
            ending = file_name.split(".")[-1]

            if ending not in ["mp3", "mp4"]:
                return False, "File ending is {0}, you should download mp3, mp4 file.".format(
                    ending
                )

            base = self.slugify(broadcast_date.split(" ")[0] + " " + video_title + " " + stub)
            if len(base) > 100:
                base = base[:100]
            new_filename = base + "." + ending

            if self.check_if_already_loaded(new_filename):
                return False, "File ./{0} is already on the disk".format(
                    self.save_directory / new_filename
                )
            self.get_save_directory(stub, broadcast_date)

            # get actual file
            msg = "Started loading file {0} with size: {1:.2f} MB.....".format(
                stub, file_size_MB
            )
            self.start_video_loading.emit(msg)
            r = requests.get(http_streamer + "/" + file_name)
            if r.status_code != 200:
                return False, "Could not load the video file."
            try:
                with open(self.save_directory / new_filename, "wb") as file:
                    file.write(r.content)
            except Exception as e:
                msg = "There was something wrong with writing to the file.\nb{0}".format(e)
                return False, msg

            msg = 'Successfully downloaded the video "{0}" which is located at "{1}"'.format(
                video_title, self.save_directory
            )
            return True, msg

    def get_save_directory(self, stub, date: Optional[str] = None) -> None:
        if self.by_week:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            year, week, _ = date_obj.isocalendar()
            add_dir = "by_week/{0}/{1:02d}/".format(year, week)
            self.save_directory = self.home_folder / add_dir
        else:
            self.save_directory = self.home_folder / stub

        # if folder does not exist we create new one
        if not self.save_directory.exists():
            self.preparation_started.emit("Had to create directory.")
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def check_if_already_loaded(self, fname):
        root = self.home_folder
        for path, subdirs, files in os.walk(root):
            for name in files:
                if name == fname:
                    self.save_directory = pathlib.Path(path).relative_to(root)
                    return True
        return False

    def rearrange_rtv_files(self, folde: pathlib.Path, by_week: bool = True):
        pass

    def check_file_size(self, response_dict):
        file_size = response_dict["response"]["mediaFiles"][0]["filesize"]
        file_size_MB = float(file_size) / 2**20
        return file_size_MB > self.file_size_tresh

    def slugify(self, value):
        """
        Normalizes string, converts to lowercase, removes non-alpha characters,
        and converts spaces to hyphens.
        """
        try:
            import unicodedata

            value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
            value = value.decode("ascii")
            value = str(re.sub("[^\w\s-]", "", value).strip().lower())
            value = str(re.sub("[-\s]+", "-", value))
            if len(value) > 128:
                value = value[:128]
            return value
        except Exception as e:
            print(e)
