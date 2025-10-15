# app/__init__.py

from flask import Flask
from app.models import close_db, get_publications_by_lecturer, get_all_lecturers
import os

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_pyfile(os.path.join(os.path.dirname(__file__), '..', 'config.py'))
    app.secret_key = app.config.get('SECRET_KEY', 'default_secret_key')

    # Регистрация blueprint'а
    from app.routes import bp
    app.register_blueprint(bp)

    # Автоматическое закрытие соединения с БД
    app.teardown_appcontext(close_db)

    # Делаем функции доступными во всех шаблонах
    app.jinja_env.globals['get_publications_by_lecturer'] = get_publications_by_lecturer
    app.jinja_env.globals['get_all_lecturers'] = get_all_lecturers

    return app
