from flask import Flask, render_template
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
import pytz
from raven.contrib.flask import Sentry

bcrypt = Bcrypt()
db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
sentry = Sentry()


def create_app(config_objects=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('esther.settings.base')
    app.config.from_pyfile('settings.py', silent=True)

    if config_objects:
        for config_object in config_objects:
            app.config.from_object(config_object)

    # Conver the time zone name into a pytz timezone and store it in the
    # config. TODO: Is there a better way to do this?
    app.config['TIME_ZONE'] = pytz.timezone(app.config['TIME_ZONE_NAME'])

    bcrypt.init_app(app)
    db.init_app(app)
    # Initialize the inter-mapper relationships of all mappers
    # see: http://docs.sqlalchemy.org/en/rel_0_8/orm/mapper_config.html#sqlalchemy.orm.configure_mappers
    db.configure_mappers()
    login_manager.init_app(app)
    mail.init_app(app)
    sentry.init_app(app)

    # Import all modules needed to create an app
    # TODO: Find a decent alternative to the unused models import (?)
    from esther import models
    from esther import filters
    from esther.views import auth
    from esther.views import blog
    from esther.views import general

    # Flask-Login settings are stored on the ``LoginManager`` instance
    auth.configure(login_manager, app)
    filters.register_all(app)

    app.register_blueprint(auth.blueprint)
    app.register_blueprint(blog.blueprint, url_prefix='/blog')
    app.register_blueprint(general.blueprint)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app
