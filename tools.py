import settings
import os

import requests

def splitlist(list_, number):
    lists = []
    last_number = 0.
    while last_number < len(list_):
        new_list = list_[int(last_number):int(last_number + \
                                              (len(list_)/float(number)))]
        lists.append(new_list)
        last_number += len(list_)/float(number)
    while len(lists) < number:
        lists.append([])
    return lists

def create_dir(name):
    if not os.path.isdir(name):
        os.makedirs(name)
        settings.logger.log("Created directory '{name}'".format(name=name))

def to_tracker(l):
    r = requests.post('http://tracker.archiveteam.org/newsgrabber/rescue-me',
                      data={'items': '\n'.join(l)})
    return r.status_code == 200
