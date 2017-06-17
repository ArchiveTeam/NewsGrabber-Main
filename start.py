import os
import threading
import time

import irc
import log
import upload
import tools
import service
import settings

def main():
    if os.path.isfile('UPDATE'):
        os.remove('UPDATE')

    settings.init()
    settings.logger = log.Log(settings.log_file_name)
    settings.logger.daemon = True
    settings.logger.start()
    settings.logger.log('Starting NewsGrabber')

    tools.create_dir(settings.dir_new_urllists)
    tools.create_dir(settings.dir_old_urllists)
    tools.create_dir(settings.dir_donefiles)
    tools.create_dir(settings.dir_ready)
    tools.create_dir(settings.dir_last_upload)
    tools.create_dir(settings.dir_dumped_url_data)

    if not os.path.isfile(settings.targets):
        settings.logger.log("Please add one or more rsync targets to file " \
                            "'{targets}'".format(targets=settings.targets),
                            'ERROR')
    if not os.path.isfile(settings.keys):
        settings.logger.log("Please add you keys by running 'add_keys.py'.",
                            'ERROR')

    settings.irc_bot = irc.IRC()
    settings.irc_bot.daemon = True
    settings.irc_bot.start()
    time.sleep(30)
    settings.upload = upload.Upload()
    settings.upload.daemon = True
    settings.upload.start()
    settings.run_services = service.RunServices()
    settings.run_services.daemon = True
    settings.run_services.start()
    
    while settings.running:
        if os.path.isfile('STOP'):
            os.remove('STOP')
            open('UPDATE', 'w').close()
            break
        time.sleep(1)

if __name__ == '__main__':
    main()