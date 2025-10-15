// app/static/js/script.js

// Подтверждение удаления
document.addEventListener('DOMContentLoaded', function() {
    let deleteForms = document.querySelectorAll('form.delete-form');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Вы уверены, что хотите удалить запись? Это действие необратимо.')) {
                e.preventDefault();
            }
        });
    });

    // Автофокус на первом видимом input/text
    let firstInput = document.querySelector('form input:not([type=hidden]), form textarea');
    if (firstInput) {
        firstInput.focus();
    }

    // Прокрутка к flash-сообщению
    let flash = document.querySelector('.flash, .alert-success, .alert-error');
    if (flash) {
        window.scrollTo({ top: flash.offsetTop - 40, behavior: 'smooth' });
    }

    // Быстрое копирование ссылки на публикацию
    let copyLinks = document.querySelectorAll('.copy-link');
    copyLinks.forEach(function(btn) {
        btn.addEventListener('click', function() {
            let url = btn.getAttribute('data-url');
            navigator.clipboard.writeText(url);
            btn.innerText = 'Скопировано!';
            setTimeout(() => { btn.innerText = 'Копировать ссылку'; }, 1500);
        });
    });
});
