import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_bootstrap import Bootstrap

from flask import Flask
from config import Config



app = Flask(__name__)
app.config.from_object(Config)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
bootstrap = Bootstrap(app)

from app import routes

