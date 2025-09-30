#!/bin/bash
set -e
echo '🚀 Выгрузка v0.8.2 на GitHub'
echo ''
if [ ! -d '.git' ]; then
  git init
  echo '✅ Git инициализирован'
fi
if ! git remote | grep -q origin; then
  echo 'Введите URL GitHub репозитория:'
  read -p 'URL: ' REPO_URL
  git remote add origin "$REPO_URL"
  echo "✅ Remote добавлен: $REPO_URL"
fi
cat > CHANGELOG.md << 'CLOG'
# Changelog

## [0.8.2] - 2025-10-01

### 🎉 Новое
- Inline кнопки категорий (по 2 в ряд)
- Прогресс-бар (Шаг X из Y)
- Кнопка Сейчас для времени
- Поддержка альбомов (1-3 фото)
- Статусы с эмодзи: 🟡🔵🟢

### ✅ Исправлено
- Возвращены ФИО и Телефон
- Логика полей транспорта
- Сохранение массива фото
- Одно сообщение при альбоме
- Кнопки Назад везде

### 🔧 Технические
- API /api/v1/photos/{file_id}
- fields_by_subcategory в config
- bot/utils/status.py
- run_dev.sh для отладки
CLOG
cat > README.md << 'RM'
# 🏙️ Городской помощник v0.8.2

Telegram бот для жалоб жителей муниципальным службам.

## 📋 Возможности

- 📝 15 категорий жалоб
- 📷 До 3 фото
- 📍 Геолокация
- 📋 Mini App для жителей
- 🎫 Канбан для служб
- 🟡🔵🟢 Статусы

## 🚀 Установка

``````

## 🛠 Разработка

``````

## 📚 Документация

- API: https://domain:8443/docs
- Структура: backend/ bot/ frontend/
- См. CHANGELOG.md

## 📄 Лицензия

MIT
RM
cat > .gitignore << 'GI'
__pycache__/
*.pyc
*.pyo
*.egg-info/
venv/
env/
.env
*.sqlite*
*.db
logs/
*.log
.vscode/
.idea/
backups/
data/
*.pem
*.key
*.crt
GI
echo ''
echo '📦 Добавление файлов...'
git add .
if git diff --cached --quiet; then
  echo 'Нет изменений'
  exit 0
fi
echo ''
echo '📋 Файлы:'
git diff --cached --name-status
echo ''
read -p 'Продолжить? (y/n) ' -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  exit 1
fi
echo ''
echo '💾 Коммит...'
git commit -m 'Release v0.8.2

✨ Новое:
- Inline кнопки категорий
- Прогресс-бар
- Поддержка альбомов
- Статусы с эмодзи

🐛 Исправлено:
- ФИО и телефон
- Логика транспорта
- Сохранение фото (JSON array)
- UX улучшения'
echo '✅ Коммит создан'
echo ''
echo '🏷️ Создание тега...'
git tag -a v0.8.2 -m 'Release v0.8.2'
echo '✅ Тег создан'
echo ''
echo '🚀 Отправка...'
git push origin main
git push origin v0.8.2
echo ''
echo '✅ Выгрузка завершена!'
echo ''
git remote get-url origin