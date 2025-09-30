#!/bin/bash
echo "🐛 Запуск в режиме отладки (логи в консоль)"
echo "Нажмите Ctrl+C для остановки"
echo ""
cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
PYTHONPATH=. poetry run python run_bot.py