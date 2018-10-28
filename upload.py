import threading
import os
import time
import re

import settings


class Upload(threading.Thread):

    """Uploading and sorting of files is done here."""

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            for d in os.listdir(settings.dir_ready):
                d = os.path.join(settings.dir_ready, d)
                if not os.path.isdir(d):
                    continue
                for f in os.listdir(d):
                    if f.startswith('.') or not f.endswith('.warc.gz'):
                        continue
                    list_search = re.search(
                        r'(warrior(?:-videos)?_[0-9]+_[0-9]{10}\.[0-9]{1,2})', f)
                    if not list_search:
                        continue
                    list_name = list_search.group(1)
                    list_location = os.path.join('warriorlists', list_name)
                    print list_location
                    if os.path.isfile(list_location):
                        os.remove(list_location)
                    os.rename(os.path.join(d, f),
                              os.path.join('megawarc', 'incoming', f))
            time.sleep(5)
