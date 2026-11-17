# Зимовий ІТ табір — портал викладача

Статичний сайт (GitHub Pages). Головна сторінка — `index.html`.

## Як додати урок
1. Покладіть HTML-файл уроку в `lessons/6-8/` або `lessons/9-12/`
   (назви на кшталт `lesson-01.html`, `lesson-02.html` — за ними сортується список).
2. Запустіть `python3 scripts/update-lessons.py` — оновиться `lessons.js`.
   Назва береться з `<title>`, опис — з `<meta name="description">` (необов'язково).
3. Закомітьте та запуште. Назви й опис можна правити вручну в `lessons.js`.

## Публікація
Settings → Pages → Deploy from a branch → гілка з `index.html`, папка `/ (root)`.
