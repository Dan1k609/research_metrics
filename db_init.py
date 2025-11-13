import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'research_metrics.db')


def create_tables(conn):
    c = conn.cursor()

    # Таблица пользователей
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            lecturer_id INTEGER
        )
    """)

    # Таблица преподавателей
    c.execute("""
        CREATE TABLE IF NOT EXISTS lecturers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT,
            position TEXT,
            department TEXT,
            academic_degree TEXT,
            orcid TEXT,
            email TEXT
        )
    """)

    # Таблица публикаций (с полями для статуса и доработок)
    c.execute("""
        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            year INTEGER,
            journal TEXT,
            source TEXT,
            link TEXT,
            citations INTEGER,
            doi TEXT,
            status TEXT DEFAULT 'new',
            review_comment TEXT,
            revision_deadline TEXT,
            reviewer_id INTEGER
        )
    """)

    # Связь публикация <-> преподаватели (many-to-many)
    c.execute("""
        CREATE TABLE IF NOT EXISTS lecturer_publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecturer_id INTEGER,
            publication_id INTEGER,
            FOREIGN KEY(lecturer_id) REFERENCES lecturers(id),
            FOREIGN KEY(publication_id) REFERENCES publications(id)
        )
    """)

    # Метрики
    c.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecturer_id INTEGER,
            year INTEGER,
            total_publications INTEGER,
            total_citations INTEGER,
            h_index INTEGER,
            rinz INTEGER,
            scopus INTEGER,
            wos INTEGER,
            gs INTEGER,
            FOREIGN KEY(lecturer_id) REFERENCES lecturers(id)
        )
    """)

    # Журнал действий
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Таблица обратной связи
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица новостей
    c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица FAQ
    c.execute("""
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT
        )
    """)

    conn.commit()


def insert_test_data(conn):
    c = conn.cursor()

    from werkzeug.security import generate_password_hash

    # Пользователи: admin/admin, user/user
    c.execute(
        "INSERT OR IGNORE INTO users (fio, email, password, role) VALUES (?, ?, ?, ?)",
        ('Администратор', 'admin@university.ru', generate_password_hash('admin'), 'admin')
    )
    c.execute(
        "INSERT OR IGNORE INTO users (fio, email, password, role) VALUES (?, ?, ?, ?)",
        ('Научный сотрудник', 'user@university.ru', generate_password_hash('user'), 'staff')
    )

    # Преподаватели (основные)
    c.execute(
        "INSERT OR IGNORE INTO lecturers (fio, position, department, academic_degree, orcid, email) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ('Иванов Иван Иванович', 'доцент', 'Кафедра информационных технологий',
         'к.т.н.', '0000-0001-2345-6789', 'ivanov@university.ru')
    )
    c.execute(
        "INSERT OR IGNORE INTO lecturers (fio, position, department, academic_degree, orcid, email) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ('Петрова Мария Сергеевна', 'профессор', 'Кафедра экономики',
         'д.э.н.', '0000-0002-3333-2222', 'petrova@university.ru')
    )
    c.execute(
        "INSERT OR IGNORE INTO lecturers (fio, position, department, academic_degree, orcid, email) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ('Сидоров Алексей Петрович', 'ассистент', 'Кафедра математики',
         '', '', 'sidorov@university.ru')
    )

    # Учётные записи для этих преподавателей (роль lecturer)
    # Предполагаем, что это первые три записи в lecturers -> id 1,2,3
    c.execute(
        "INSERT OR IGNORE INTO users (fio, email, password, role, lecturer_id) "
        "VALUES (?, ?, ?, ?, ?)",
        ('Иванов Иван Иванович', 'ivanov@university.ru',
         generate_password_hash('ivanov'), 'lecturer', 1)
    )
    c.execute(
        "INSERT OR IGNORE INTO users (fio, email, password, role, lecturer_id) "
        "VALUES (?, ?, ?, ?, ?)",
        ('Петрова Мария Сергеевна', 'petrova@university.ru',
         generate_password_hash('petrova'), 'lecturer', 2)
    )
    c.execute(
        "INSERT OR IGNORE INTO users (fio, email, password, role, lecturer_id) "
        "VALUES (?, ?, ?, ?, ?)",
        ('Сидоров Алексей Петрович', 'sidorov@university.ru',
         generate_password_hash('sidorov'), 'lecturer', 3)
    )

    # Тестовый преподаватель для личного кабинета
    c.execute(
        "INSERT INTO lecturers (fio, position, department, academic_degree, orcid, email) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ('Тестовый Преподаватель', 'доцент', 'Кафедра информатики',
         'к.т.н.', '0000-0000-0000-0000', 'lecturer@university.ru')
    )
    test_lecturer_id = c.lastrowid

    # Пользователь, связанный с этим преподавателем (роль lecturer)
    c.execute(
        "INSERT INTO users (fio, email, password, role, lecturer_id) VALUES (?, ?, ?, ?, ?)",
        ('Тестовый Преподаватель', 'lecturer@university.ru',
         generate_password_hash('lecturer'), 'lecturer', test_lecturer_id)
    )

    # Публикации
    c.execute(
        "INSERT OR IGNORE INTO publications "
        "(title, year, journal, source, link, citations, doi) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('Моделирование процессов обработки данных', 2023, 'Информатика и образование',
         'РИНЦ', 'https://elibrary.ru/example1', 5, '10.1234/example1')
    )
    c.execute(
        "INSERT OR IGNORE INTO publications "
        "(title, year, journal, source, link, citations, doi) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('Экономический анализ инноваций', 2022, 'Экономика и управление',
         'Scopus', 'https://scopus.com/example2', 10, '10.1234/example2')
    )
    c.execute(
        "INSERT OR IGNORE INTO publications "
        "(title, year, journal, source, link, citations, doi) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('Современные методы обучения', 2021, 'Педагогика XXI века',
         'WoS', '', 3, '10.1234/example3')
    )

    # Связи публикаций и преподавателей
    c.execute(
        "INSERT OR IGNORE INTO lecturer_publications (lecturer_id, publication_id) VALUES (?, ?)",
        (1, 1)
    )
    c.execute(
        "INSERT OR IGNORE INTO lecturer_publications (lecturer_id, publication_id) VALUES (?, ?)",
        (2, 2)
    )
    c.execute(
        "INSERT OR IGNORE INTO lecturer_publications (lecturer_id, publication_id) VALUES (?, ?)",
        (3, 3)
    )
    c.execute(
        "INSERT OR IGNORE INTO lecturer_publications (lecturer_id, publication_id) VALUES (?, ?)",
        (1, 2)
    )
    c.execute(
        "INSERT OR IGNORE INTO lecturer_publications (lecturer_id, publication_id) VALUES (?, ?)",
        (2, 1)
    )

    # Метрики
    c.execute(
        "INSERT OR IGNORE INTO metrics "
        "(lecturer_id, year, total_publications, total_citations, h_index, rinz, scopus, wos, gs) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (1, 2023, 7, 24, 3, 5, 1, 1, 0)
    )
    c.execute(
        "INSERT OR IGNORE INTO metrics "
        "(lecturer_id, year, total_publications, total_citations, h_index, rinz, scopus, wos, gs) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (2, 2023, 12, 54, 6, 2, 8, 2, 0)
    )
    c.execute(
        "INSERT OR IGNORE INTO metrics "
        "(lecturer_id, year, total_publications, total_citations, h_index, rinz, scopus, wos, gs) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (3, 2023, 3, 6, 1, 0, 0, 1, 2)
    )

    # Тестовые обращения
    c.execute(
        "INSERT OR IGNORE INTO feedback (name, email, message) VALUES (?, ?, ?)",
        ('Василий', 'vasya@example.com', 'Не работает фильтрация в списке публикаций')
    )
    c.execute(
        "INSERT OR IGNORE INTO feedback (name, email, message) VALUES (?, ?, ?)",
        ('Екатерина', 'katya@example.com', 'Хочу предложить добавить экспорт в Excel')
    )
    c.execute(
        "INSERT OR IGNORE INTO feedback (name, email, message) VALUES (?, ?, ?)",
        ('Степан', 'stepan@example.com', 'Опечатка на странице преподавателей')
    )

    # Тестовые новости
    c.execute(
        "INSERT OR IGNORE INTO news (title, content) VALUES (?, ?)",
        ('Портал обновлён!', 'Добавлен раздел обратной связи, исправлены мелкие ошибки и улучшена навигация.')
    )
    c.execute(
        "INSERT OR IGNORE INTO news (title, content) VALUES (?, ?)",
        ('Запуск портала научных публикаций',
         'Сервис запущен для учёта и аналитики научных публикаций преподавателей университета.')
    )

    # Тестовые FAQ
    c.execute(
        "INSERT OR IGNORE INTO faq (question, answer) VALUES (?, ?)",
        ('Как добавить публикацию?',
         'Авторизуйтесь как сотрудник, затем перейдите в раздел "Публикации" и нажмите "Добавить публикацию".')
    )
    c.execute(
        "INSERT OR IGNORE INTO faq (question, answer) VALUES (?, ?)",
        ('Кто может видеть мои публикации?',
         'Вся информация о публикациях доступна для просмотра всем пользователям портала, включая гостей.')
    )

    conn.commit()


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    insert_test_data(conn)
    conn.close()
    print(f"База данных успешно создана и заполнена тестовыми данными: {DB_PATH}")


if __name__ == '__main__':
    main()
