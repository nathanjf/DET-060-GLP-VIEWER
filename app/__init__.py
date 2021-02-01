'''
    Creates the app 
'''

# Import dependencies
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_apscheduler import APScheduler

# Import configuration
from .config import Config

# Create the database and login manager
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
sched = APScheduler()
'''
    Creates the app
'''

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)
    
    db.app = app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = 'main.login'

    from .main import job1, job2
    sched.start()

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
