from shioaji_app.kbar_processor import conn, KBarConsumer


if __name__ == '__main__':
    worker = KBarConsumer(conn, 'kbar')
    worker.run()