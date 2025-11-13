import csv
from io import StringIO
from flask import Response
from flask import Blueprint, render_template, redirect, url_for, request, session, flash, g
from app.models import *
from functools import wraps
from datetime import date


bp = Blueprint('main', __name__)

# --- Авторизация и контроль доступа ---

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('main.login'))
            if role and session.get('role') != role:
                flash('Нет доступа')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = get_user_by_id(user_id) if user_id else None

# --- Аутентификация ---

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_user_by_email(request.form['email'])
        if user and check_user_password(user, request.form['password']):
            session['user_id'] = user['id']
            session['role'] = user['role']
            log_action(user['id'], "login", "Вход в систему")
            return redirect(url_for('main.dashboard'))
        flash('Неверный email или пароль')
    return render_template('login.html')

@bp.route('/logout')
@login_required()
def logout():
    log_action(session['user_id'], "logout", "Выход из системы")
    session.clear()
    return redirect(url_for('main.login'))

# --- Дашборд и главная страница ---

@bp.route('/')
@login_required()
def dashboard():
    lecturers = get_all_lecturers()
    pubs = get_all_publications()
    metrics = {}
    for l in lecturers:
        m = get_metrics_by_lecturer(l['id'])
        metrics[l['id']] = m[0] if m else None
    feedback_list = []
    if g.user and g.user['role'] == 'admin':
        feedback_list = get_all_feedback()
    return render_template('dashboard.html', lecturers=lecturers, pubs=pubs, metrics=metrics, feedback_list=feedback_list)

@bp.route('/admin/export_dashboard')
@login_required(role='admin')
def export_dashboard():
    lecturers = get_all_lecturers()
    pubs = get_all_publications()
    feedbacks = get_all_feedback()

    # Генерируем CSV "на лету"
    output = StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    # --- Преподаватели ---
    writer.writerow(['Преподаватели'])
    writer.writerow(['ID', 'ФИО', 'Кафедра', 'Должность', 'Учёная степень', 'ORCID', 'Email'])
    for l in lecturers:
        writer.writerow([l['id'], l['fio'], l['department'], l['position'], l['academic_degree'], l['orcid'], l['email']])
    writer.writerow([])

    # --- Публикации ---
    writer.writerow(['Публикации'])
    writer.writerow(['ID', 'Название', 'Год', 'Журнал', 'Источник', 'Ссылка', 'Цитирования', 'DOI'])
    for p in pubs:
        writer.writerow([p['id'], p['title'], p['year'], p['journal'], p['source'], p['link'], p['citations'], p['doi']])
    writer.writerow([])

    # --- Обращения пользователей ---
    writer.writerow(['Обращения (обратная связь)'])
    writer.writerow(['ID', 'Имя', 'Email', 'Сообщение', 'Дата'])
    for f in feedbacks:
        writer.writerow([f['id'], f['name'], f['email'], f['message'], f['created_at']])
    writer.writerow([])

    output.seek(0)
    # Формируем правильный заголовок для скачивания
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=dashboard_export.csv"}
    )

# --- Форма обратной связи ---

@bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        if name and email and message:
            create_feedback(name, email, message)
            flash("Спасибо! Ваше сообщение отправлено администрации.")
            return redirect(url_for('main.feedback'))
        else:
            flash("Пожалуйста, заполните все поля.")
    return render_template('feedback.html')

# --- Просмотр обращений администратора ---

@bp.route('/admin/feedback')
@login_required(role='admin')
def admin_feedback():
    feedback_list = get_all_feedback()
    return render_template('admin_feedback.html', feedbacks=feedback_list)

# --- Преподаватели (Открытые страницы) ---

@bp.route('/lecturers')
def lecturers():
    lecturers = get_all_lecturers()
    return render_template('lecturers.html', lecturers=lecturers)

@bp.route('/lecturer/<int:lecturer_id>')
def lecturer_profile(lecturer_id):
    lecturer = get_lecturer_by_id(lecturer_id)
    pubs = get_publications_by_lecturer(lecturer_id)
    metrics = get_metrics_by_lecturer(lecturer_id)
    return render_template('lecturer_profile.html', lecturer=lecturer, pubs=pubs, metrics=metrics)

@bp.route('/add_lecturer', methods=['GET', 'POST'])
@login_required(role='admin')
def add_lecturer():
    if request.method == 'POST':
        create_lecturer(
            request.form['fio'], request.form['position'], request.form['department'],
            request.form['academic_degree'], request.form['orcid'], request.form['email']
        )
        log_action(session['user_id'], "add_lecturer", f"Добавлен преподаватель: {request.form['fio']}")
        return redirect(url_for('main.lecturers'))
    return render_template('add_lecturer.html')

@bp.route('/edit_lecturer/<int:lecturer_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_lecturer(lecturer_id):
    lecturer = get_lecturer_by_id(lecturer_id)
    if request.method == 'POST':
        update_lecturer(
            lecturer_id,
            request.form['fio'], request.form['position'], request.form['department'],
            request.form['academic_degree'], request.form['orcid'], request.form['email']
        )
        log_action(session['user_id'], "edit_lecturer", f"Изменён преподаватель: {request.form['fio']}")
        return redirect(url_for('main.lecturers'))
    return render_template('edit_lecturer.html', lecturer=lecturer)

@bp.route('/delete_lecturer/<int:lecturer_id>', methods=['POST'])
@login_required(role='admin')
def delete_lecturer_route(lecturer_id):
    lecturer = get_lecturer_by_id(lecturer_id)
    delete_lecturer(lecturer_id)
    log_action(session['user_id'], "delete_lecturer", f"Удалён преподаватель: {lecturer['fio']}")
    return redirect(url_for('main.lecturers'))

# --- Публикации (Открытая страница) ---

@bp.route('/publications')
def publications():
    pubs = get_all_publications()
    return render_template('publications.html', pubs=pubs)

@bp.route('/add_publication', methods=['GET', 'POST'])
@login_required(role='admin')
def add_publication():
    lecturers = get_all_lecturers()
    if request.method == 'POST':
        lecturer_ids = request.form.getlist('lecturer_ids')
        create_publication(
            request.form['title'], request.form['year'], request.form['journal'],
            request.form['source'], request.form['link'], request.form['citations'],
            request.form['doi'], [int(lid) for lid in lecturer_ids]
        )
        log_action(session['user_id'], "add_publication", f"Добавлена публикация: {request.form['title']}")
        return redirect(url_for('main.publications'))
    return render_template('add_publication.html', lecturers=lecturers)

@bp.route('/edit_publication/<int:pub_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_publication(pub_id):
    pub, current_lecturers = get_publication_by_id(pub_id)
    lecturers = get_all_lecturers()
    current_ids = [l['id'] for l in current_lecturers]
    if request.method == 'POST':
        lecturer_ids = request.form.getlist('lecturer_ids')
        update_publication(
            pub_id,
            request.form['title'], request.form['year'], request.form['journal'],
            request.form['source'], request.form['link'], request.form['citations'],
            request.form['doi'], [int(lid) for lid in lecturer_ids]
        )
        log_action(session['user_id'], "edit_publication", f"Изменена публикация: {request.form['title']}")
        return redirect(url_for('main.publications'))
    return render_template('edit_publication.html', pub=pub, lecturers=lecturers, current_ids=current_ids)

@bp.route('/delete_publication/<int:pub_id>', methods=['POST'])
@login_required(role='admin')
def delete_publication_route(pub_id):
    pub, _ = get_publication_by_id(pub_id)
    delete_publication(pub_id)
    log_action(session['user_id'], "delete_publication", f"Удалена публикация: {pub['title']}")
    return redirect(url_for('main.publications'))

# --- Метрики ---

@bp.route('/metrics/<int:lecturer_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def metrics(lecturer_id):
    lecturer = get_lecturer_by_id(lecturer_id)
    metrics = get_metrics_by_lecturer(lecturer_id)
    if request.method == 'POST':
        set_metrics(
            lecturer_id,
            int(request.form['year']),
            int(request.form['total_publications']),
            int(request.form['total_citations']),
            int(request.form['h_index']),
            int(request.form['rinz']),
            int(request.form['scopus']),
            int(request.form['wos']),
            int(request.form['gs'])
        )
        log_action(session['user_id'], "edit_metrics", f"Обновлены метрики: {lecturer['fio']} ({request.form['year']})")
        return redirect(url_for('main.lecturer_profile', lecturer_id=lecturer_id))
    return render_template('metrics.html', lecturer=lecturer, metrics=metrics)

# --- Отчёты (Открытая страница) ---

@bp.route('/reports')
def reports():
    lecturers = get_all_lecturers()
    pubs = get_all_publications()
    # Простая аналитика: количество публикаций, цитирований по кафедрам/годам
    departments = {}
    for l in lecturers:
        dep = l['department']
        if dep not in departments:
            departments[dep] = {'lecturers': [], 'publications': 0, 'citations': 0}
        departments[dep]['lecturers'].append(l)
        pubs_by_l = get_publications_by_lecturer(l['id'])
        departments[dep]['publications'] += len(pubs_by_l)
        departments[dep]['citations'] += sum([int(p['citations']) for p in pubs_by_l if p['citations']])
    return render_template('reports.html', departments=departments, pubs=pubs)

# --- Логи ---

@bp.route('/log')
@login_required(role='admin')
def log():
    logs = get_all_logs()
    return render_template('log.html', logs=logs)

# --- Новости ---

@bp.route('/news')
def news_list():
    news = get_all_news()
    return render_template('news.html', news=news)

@bp.route('/news/<int:news_id>')
def news_detail(news_id):
    news = get_news_by_id(news_id)
    if not news:
        flash("Новость не найдена.")
        return redirect(url_for('main.news_list'))
    return render_template('news_detail.html', news=news)

# --- FAQ ---

@bp.route('/faq')
def faq():
    faqs = get_all_faq()
    return render_template('faq.html', faqs=faqs)

# --- Админ-панель: Новости ---

@bp.route('/admin/news', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_news():
    news = get_all_news()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            create_news(title, content)
            flash('Новость добавлена!')
            return redirect(url_for('main.admin_news'))
        else:
            flash('Заполните все поля.')
    return render_template('admin_news.html', news=news)

@bp.route('/admin/news/delete/<int:news_id>', methods=['POST'])
@login_required(role='admin')
def delete_news_route(news_id):
    delete_news(news_id)
    flash('Новость удалена.')
    return redirect(url_for('main.admin_news'))

# --- Админ-панель: FAQ ---

@bp.route('/admin/faq', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_faq():
    faqs = get_all_faq()
    if request.method == 'POST':
        question = request.form.get('question')
        answer = request.form.get('answer')
        if question and answer:
            create_faq(question, answer)
            flash('Вопрос добавлен!')
            return redirect(url_for('main.admin_faq'))
        else:
            flash('Заполните оба поля.')
    return render_template('admin_faq.html', faqs=faqs)

@bp.route('/admin/faq/delete/<int:faq_id>', methods=['POST'])
@login_required(role='admin')
def delete_faq_route(faq_id):
    delete_faq(faq_id)
    flash('Вопрос удалён.')
    return redirect(url_for('main.admin_faq'))

@bp.route('/profile')
@login_required()
def profile():
    user = g.user

    users = []
    pending_pubs = []
    revision_pubs = []

    if user['role'] == 'admin':
        users = get_all_users()
    elif user['role'] == 'staff':
        pending_pubs = get_publications_for_review()
        revision_pubs = get_publications_with_revision_required()

    return render_template(
        'profile.html',
        user=user,
        users=users,
        pending_pubs=pending_pubs,
        revision_pubs=revision_pubs
    )


# --- Управление пользователями ---
@bp.route('/admin/add_user', methods=['GET', 'POST'])
@login_required(role='admin')
def add_user():
    if request.method == 'POST':
        fio = request.form['fio']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        if fio and email and password and role:
            create_user(fio, email, password, role)
            flash('Пользователь добавлен')
            return redirect(url_for('main.profile'))
        else:
            flash('Заполните все поля')
    return render_template('add_user.html')

@bp.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_user(user_id):
    user = get_user_by_id(user_id)
    if request.method == 'POST':
        fio = request.form['fio']
        email = request.form['email']
        role = request.form['role']
        update_user(user_id, fio, email, role)
        flash('Данные пользователя обновлены')
        return redirect(url_for('main.profile'))
    return render_template('edit_user.html', user=user)

@bp.route('/admin/block_user/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def block_user(user_id):
    user = get_user_by_id(user_id)
    update_user(user_id, user['fio'], user['email'], 'blocked')
    flash('Пользователь заблокирован')
    return redirect(url_for('main.profile'))

@bp.route('/admin/unblock_user/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def unblock_user(user_id):
    user = get_user_by_id(user_id)
    update_user(user_id, user['fio'], user['email'], 'staff')
    flash('Пользователь разблокирован')
    return redirect(url_for('main.profile'))

@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def delete_user_route(user_id):
    delete_user(user_id)
    flash('Пользователь удалён')
    return redirect(url_for('main.profile'))

# --- Кабинет сотрудника научного отдела: проверка публикаций ---

@bp.route('/staff/review')
@login_required(role='staff')
def staff_review():
    pubs = get_publications_for_review()
    today = date.today().isoformat()  # 'YYYY-MM-DD'
    return render_template('staff_review.html', pubs=pubs, today=today)

@bp.route('/staff/publication/<int:pub_id>/approve', methods=['POST'])
@login_required(role='staff')
def staff_approve_publication(pub_id):
    comment = request.form.get('comment') or None
    update_publication_status(
        pub_id,
        status='approved',
        review_comment=comment,
        revision_deadline=None,
        reviewer_id=session['user_id']
    )
    flash('Публикация утверждена')
    return redirect(url_for('main.staff_review'))


@bp.route('/staff/publication/<int:pub_id>/reject', methods=['POST'])
@login_required(role='staff')
def staff_reject_publication(pub_id):
    comment = request.form.get('comment') or None
    update_publication_status(
        pub_id,
        status='rejected',
        review_comment=comment,
        revision_deadline=None,
        reviewer_id=session['user_id']
    )
    flash('Публикация отклонена')
    return redirect(url_for('main.staff_review'))


@bp.route('/staff/publication/<int:pub_id>/send_to_revision', methods=['POST'])
@login_required(role='staff')
def staff_send_to_revision(pub_id):
    comment = request.form.get('comment') or None
    deadline = request.form.get('revision_deadline') or None  # 'YYYY-MM-DD'
    update_publication_status(
        pub_id,
        status='revision_required',
        review_comment=comment,
        revision_deadline=deadline,
        reviewer_id=session['user_id']
    )
    flash('Публикация отправлена на доработку')
    return redirect(url_for('main.staff_review'))
@bp.route('/staff/export_reports')
@login_required(role='staff')
def staff_export_reports():
    pubs = get_all_publications()

    output = StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        'ID', 'Название', 'Год', 'Журнал', 'Статус',
        'Цитирования', 'DOI', 'Крайний срок доработки', 'Комментарий проверяющего'
    ])

    for p in pubs:
        # sqlite3.Row, поэтому доступ через [].
        # Поля status/revision_deadline/review_comment будут, если ты прогнал create_tables().
        status = p['status'] if 'status' in p.keys() else ''
        deadline = p['revision_deadline'] if 'revision_deadline' in p.keys() else ''
        comment = p['review_comment'] if 'review_comment' in p.keys() else ''

        writer.writerow([
            p['id'],
            p['title'],
            p['year'],
            p['journal'],
            status,
            p['citations'],
            p['doi'],
            deadline,
            comment
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=publications_report.csv"}
    )


# --- Функции для работы с обратной связью ---

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
