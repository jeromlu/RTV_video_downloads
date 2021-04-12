from rtv_video_downloader.__main__ import launch_app


if __name__ == "__main__":
    import sys
    from rtv_video_downloader.video_downloader import exception_hook

    sys.excepthook = exception_hook
    launch_app()
