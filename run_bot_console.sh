#!/bin/bash
# Запуск бота в консоли для отладки

echo "🐛 Режим отладки - логи в консоль"
echo "Нажмите Ctrl+C для остановки"
echo ""

cd "$(dirname "$0")"
PYTHONPATH=. poetry run python run_bot.py
