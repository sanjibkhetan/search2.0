from __future__ import absolute_import
import os
import re
import sys
from pathlib import Path
import webs.WebService as WebService
import traceback
def creat_app():
    try:
    ## init globals for job
        params = {
            'FLASK_AUTH_ALL'      : False,
            'FLASK_HTPASSWD_PATH'  : os.getenv('FLASK_HTPASSWD_PATH' , 'example/.htpasswd'),
            'FLASK_AUTH_REALM'     : os.getenv('FLASK_AUTH_REALM'    , 'Please Enter Valid Creds'),
            'APP_CALLBACK_URL'     : os.getenv('APP_CALLBACK_URL' ),
            'APP_CALLBACK_USER'    : os.getenv('APP_CALLBACK_USER' ),
            'APP_CALLBACK_PASS'    : os.getenv('APP_CALLBACK_PASS' ),
            'APP_SERVER_NAME'      : os.getenv('APP_SERVER_NAME' , os.uname().nodename ),
            'APP_HTTP_HOST'        : os.getenv('APP_HTTP_HOST'),
            'APP_HTTP_PORT'        : os.getenv('APP_HTTP_PORT')
        }
        app = WebService(params)
        app.run()
    except OSError as err:
        print("OS error: {0}".format(err))
    except ValueError as ve:
        print(ve)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        print("Unexpected error:", sys.exc_info())
        print(traceback.print_exc())

if __name__ == '__main__':
	creat_app()