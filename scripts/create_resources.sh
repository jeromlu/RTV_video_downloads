source ./venv/Scripts/activate
pyrcc6 -o qrc_resources.py data/resources.qrc
mv qrc_resources.py src/rtv_video_downloader
