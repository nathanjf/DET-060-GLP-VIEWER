import os

# Set basedir for the config
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    #Secret Key Configurations NOT NEEDED AS THERES NO PASSWORDS OR USER IDENTIFICATION
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'temporary string' 

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False