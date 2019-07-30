import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SEND_FILE_MAX_AGE_DEFAULT = 0