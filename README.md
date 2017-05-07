# Thanatos
WebApp for a challenge Website called Thanatos. WIP.

Running this Application
-------------
To run with debugging activated run 'run.py'. NEVER DO THIS ON A PRODUCTION SERVER.

To run with debugging only to a logfile run 'production.py'.

You'll need a file called config.py with the following content:

>- import os
basedir = os.path.abspath(os.path.dirname(__file__))
>- SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db') #where your database lives
>- SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repo') #where youre database migrations are stored
>- WHOOSH_BASE = os.path.join(basedir, 'search.db') #where the database for full text search is stored
>- WTF_CSRF_ENABLED = True #CRSF Protection enabled is usually a good idea
>- SECRET_KEY = 'you-will-never-guess' #should be long and hard to guess

>- USER_PER_PAGE = 3 #set this as you like
>- MAX_SEARCH_RESULTS = 50 #set this as you like
>- OAUTH_CREDENTIALS={
'your_provider':{
    'id':'your id',
    'secret':'your key or secret'
}
}

You can add providers by adding subclassesin oauth.py and adding the credentials to this dictionary
