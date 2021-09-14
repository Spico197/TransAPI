import time
import threading

from crawler import run as crawler_run
from webapi import run as webapi_run
from webapi import APIMiddleware
from config import configger


def watch_thread():
    while True:
        try:
            google_storage_length = api_mdw.get_len('ggl')
            nongoogle_storage_length = api_mdw.get_len('non')
            if google_storage_length < configger.STORAGE_LOWER_BOUND \
                or nongoogle_storage_length < configger.STORAGE_LOWER_BOUND:
                handler = threading.Thread(target=crawler_run)
                handler.start()
                handler.join()
                # pass
            time.sleep(configger.STORAGE_WATCH_SLEEP_TIME)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    api_mdw = APIMiddleware()

    api_handler = threading.Thread(target=webapi_run)
    watch_handler = threading.Thread(target=watch_thread)
    
    api_handler.start()
    time.sleep(2)
    watch_handler.start()
    