# app/models.py

import sqlite3
from flask import g
from werkzeug.security import generate_password_hash, check_password_hash
import os

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'research_metrics.db')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# ==== USERS ====
def create_user(fio, email, password, role):
    db = get_db()
    pw_hash = generate_password_hash(password)
    db.execute(
        "INSERT INTO users (fio, email, password, role) VALUES (?, ?, ?, ?)",
        (fio, email, pw_hash, role)
    )
    db.commit()


def get_user_by_email(email):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    return user


def get_user_by_id(user_id):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return user


def check_user_password(user, password):
    return check_password_hash(user["password"], password)


def get_all_users():
    db = get_db()
    return db.execute(
        "SELECT * FROM users"
    ).fetchall()


def update_user(user_id, fio, email, role):
    db = get_db()
    db.execute(
        "UPDATE users SET fio = ?, email = ?, role = ? WHERE id = ?",
        (fio, email, role, user_id)
    )
    db.commit()


def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()


# ==== LECTURERS ====
def create_lecturer(fio, position, department, academic_degree, orcid, email):
    db = get_db()
    db.execute(
        "INSERT INTO lecturers (fio, position, department, academic_degree, orcid, email) VALUES (?, ?, ?, ?, ?, ?)",
        (fio, position, department, academic_degree, orcid, email)
    )
    db.commit()


def get_lecturer_by_id(lecturer_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM lecturers WHERE id = ?", (lecturer_id,)
    ).fetchone()


def get_all_lecturers():
    db = get_db()
    return db.execute(
        "SELECT * FROM lecturers"
    ).fetchall()


def update_lecturer(lecturer_id, fio, position, department, academic_degree, orcid, email):
    db = get_db()
    db.execute(
        "UPDATE lecturers SET fio = ?, position = ?, department = ?, academic_degree = ?, orcid = ?, email = ? WHERE id = ?",
        (fio, position, department, academic_degree, orcid, email, lecturer_id)
    )
    db.commit()


def delete_lecturer(lecturer_id):
    db = get_db()
    db.execute("DELETE FROM lecturers WHERE id = ?", (lecturer_id,))
    db.commit()


# ==== PUBLICATIONS ====
def create_publication(title, year, journal, source, link, citations, doi, lecturer_ids):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO publications (title, year, journal, source, link, citations, doi) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, year, journal, source, link, citations, doi)
    )
    pub_id = cursor.lastrowid
    # Привязка к преподавателям
    for lid in lecturer_ids:
        cursor.execute(
            "INSERT INTO lecturer_publications (lecturer_id, publication_id) VALUES (?, ?)",
            (lid, pub_id)
        )
    db.commit()


def get_publication_by_id(pub_id):
    db = get_db()
    pub = db.execute(
        "SELECT * FROM publications WHERE id = ?", (pub_id,)
    ).fetchone()
    # Получить преподавателей
    lecturers = db.execute(
        "SELECT l.* FROM lecturers l "
        "JOIN lecturer_publications lp ON l.id = lp.lecturer_id "
        "WHERE lp.publication_id = ?", (pub_id,)
    ).fetchall()
    return pub, lecturers


def get_all_publications():
    db = get_db()
    pubs = db.execute(
        "SELECT * FROM publications ORDER BY year DESC"
    ).fetchall()
    return pubs


def get_publications_by_lecturer(lecturer_id):
    db = get_db()
    pubs = db.execute(
        "SELECT p.* FROM publications p "
        "JOIN lecturer_publications lp ON p.id = lp.publication_id "
        "WHERE lp.lecturer_id = ? ORDER BY p.year DESC",
        (lecturer_id,)
    ).fetchall()
    return pubs


def update_publication(pub_id, title, year, journal, source, link, citations, doi, lecturer_ids):
    db = get_db()
    db.execute(
        "UPDATE publications SET title = ?, year = ?, journal = ?, source = ?, link = ?, citations = ?, doi = ? WHERE id = ?",
        (title, year, journal, source, link, citations, doi, pub_id)
    )
    # Сначала удалить старые связи
    db.execute("DELETE FROM lecturer_publications WHERE publication_id = ?", (pub_id,))
    # Добавить новые связи
    for lid in lecturer_ids:
        db.execute(
            "INSERT INTO lecturer_publications (lecturer_id, publication_id) VALUES (?, ?)",
            (lid, pub_id)
        )
    db.commit()


def delete_publication(pub_id):
    db = get_db()
    db.execute("DELETE FROM lecturer_publications WHERE publication_id = ?", (pub_id,))
    db.execute("DELETE FROM publications WHERE id = ?", (pub_id,))
    db.commit()


# ==== METRICS ====
def set_metrics(lecturer_id, year, total_publications, total_citations, h_index, rinz, scopus, wos, gs):
    db = get_db()
    exists = db.execute(
        "SELECT * FROM metrics WHERE lecturer_id = ? AND year = ?",
        (lecturer_id, year)
    ).fetchone()
    if exists:
        db.execute(
            "UPDATE metrics SET total_publications=?, total_citations=?, h_index=?, rinz=?, scopus=?, wos=?, gs=? "
            "WHERE lecturer_id=? AND year=?",
            (total_publications, total_citations, h_index, rinz, scopus, wos, gs, lecturer_id, year)
        )
    else:
        db.execute(
            "INSERT INTO metrics (lecturer_id, year, total_publications, total_citations, h_index, rinz, scopus, wos, gs) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (lecturer_id, year, total_publications, total_citations, h_index, rinz, scopus, wos, gs)
        )
    db.commit()


def get_metrics_by_lecturer(lecturer_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM metrics WHERE lecturer_id = ? ORDER BY year DESC",
        (lecturer_id,)
    ).fetchall()


# ==== LOGGING ====
def log_action(user_id, action, description):
    db = get_db()
    db.execute(
        "INSERT INTO logs (user_id, action, description) VALUES (?, ?, ?)",
        (user_id, action, description)
    )
    db.commit()


def get_all_logs():
    db = get_db()
    return db.execute(
        "SELECT logs.*, u.fio AS user_fio FROM logs "
        "LEFT JOIN users u ON logs.user_id = u.id "
        "ORDER BY logs.timestamp DESC"
    ).fetchall()

# ==== FEEDBACK ====
def create_feedback(name, email, message):
    db = get_db()
    db.execute(
        "INSERT INTO feedback (name, email, message) VALUES (?, ?, ?)",
        (name, email, message)
    )
    db.commit()

def get_all_feedback():
    db = get_db()
    return db.execute(
        "SELECT * FROM feedback ORDER BY created_at DESC"
    ).fetchall()

def delete_feedback(feedback_id):
    db = get_db()
    db.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    db.commit()
