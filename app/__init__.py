from flask import Flask
from flask_login import LoginManager
from config import basedir, ADMINS, MAIL_PORT, MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD
from flask_sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'


from app import views,models
