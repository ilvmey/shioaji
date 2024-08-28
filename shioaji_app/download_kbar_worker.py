from shioaji_app.kbar_processor import conn, DownloadKBarConsumer


if __name__ == '__main__':
    worker = DownloadKBarConsumer(conn, 'download_kbar')
    worker.run()