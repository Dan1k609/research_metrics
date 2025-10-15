# app/utils.py

import re
import random
import string
from datetime import datetime
import csv
from io import StringIO
from flask import Response

def is_valid_email(email):
    """Проверка корректности email"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def is_valid_year(year):
    """Проверка, что год реалистичен (1900 <= год <= текущий)"""
    try:
        year = int(year)
        now = datetime.now().year
        return 1900 <= year <= now
    except Exception:
        return False

def format_date(dt_str, fmt_in='%Y-%m-%d %H:%M:%S', fmt_out='%d.%m.%Y %H:%M'):
    """Форматирование даты для отображения"""
    try:
        dt = datetime.strptime(dt_str, fmt_in)
        return dt.strftime(fmt_out)
    except Exception:
        return dt_str

def generate_password(length=8):
    """Генерация простого пароля"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def export_publications_csv(publications, lecturers_dict):
    """
    Генерация CSV-отчета по публикациям.
    publications: список публикаций (Row-объекты)
    lecturers_dict: dict {pub_id: [FIO, ...]}
    Возвращает Flask Response с csv.
    """
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Название', 'Год', 'Журнал', 'Источник', 'Ссылка', 'Цитирования', 'DOI/ID', 'Авторы'])
    for pub in publications:
        authors = ', '.join(lecturers_dict.get(pub['id'], []))
        writer.writerow([
            pub['id'], pub['title'], pub['year'], pub['journal'],
            pub['source'], pub['link'], pub['citations'], pub['doi'], authors
        ])
    output = si.getvalue()
    si.close()
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=publications.csv"}
    )

def safe_int(val, default=0):
    """Попытка привести к int без выброса ошибки"""
    try:
        return int(val)
    except Exception:
        return default

# Дополняй, если потребуется!
