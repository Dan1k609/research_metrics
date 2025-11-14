# app/__init__.py

from flask import Flask
from app.models import close_db, get_publications_by_lecturer, get_all_lecturers
import os

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_pyfile(os.path.join(os.path.dirname(__file__), '..', 'config.py'))
    app.secret_key = app.config.get('SECRET_KEY', 'default_secret_key')

    # === Настройки для загрузки файлов публикаций ===
    # Базовая директория проекта (папка research_metrics)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Папка, где будут лежать файлы публикаций
    upload_folder = os.path.join(base_dir, 'uploads', 'publications')
    os.makedirs(upload_folder, exist_ok=True)

    app.config['UPLOAD_FOLDER'] = upload_folder
    # Ограничение размера загружаемого файла (например, 16 МБ)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Регистрация blueprint'а
    from app.routes import bp
    app.register_blueprint(bp)

    # Автоматическое закрытие соединения с БД
    app.teardown_appcontext(close_db)

    # Делаем функции доступными во всех шаблонах
    app.jinja_env.globals['get_publications_by_lecturer'] = get_publications_by_lecturer
    app.jinja_env.globals['get_all_lecturers'] = get_all_lecturers

    return app
