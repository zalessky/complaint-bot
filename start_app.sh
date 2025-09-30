#!/bin/bash
echo "🚀 Запуск Городской помощник v0.7..."

if ! poetry --version > /dev/null 2>&1; then
    echo "❌ Poetry не установлен"
    exit 1
fi

if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Скопируйте .env.example и настройте"
    exit 1
fi

mkdir -p data logs

echo "📦 Применение миграций..."
poetry run python migrations/update_db.py

echo "🔧 Запуск Backend..."
PYTHONPATH=. poetry run python backend/main.py > logs/backend.log 2>&1 &
echo $! > logs/backend.pid
echo "Backend PID: $(cat logs/backend.pid)"

sleep 2

echo "🤖 Запуск Telegram Bot..."
PYTHONPATH=. poetry run python run_bot.py > logs/bot.log 2>&1 &
#PYTHONPATH=. poetry run python bot/bot.py > logs/bot.log 2>&1 &
echo $! > logs/bot.pid
echo "Bot PID: $(cat logs/bot.pid)"

echo ""
echo "✅ Приложение запущено!"
echo "📊 API Docs: http://localhost:8000/docs"
echo "📱 TWA Жителей: http://localhost:8000/webapp/residents"
echo "🎫 TWA Служб: http://localhost:8000/webapp/services"
echo ""
echo "Логи: tail -f logs/backend.log logs/bot.log"
echo "Остановка: bash stop_app.sh"
