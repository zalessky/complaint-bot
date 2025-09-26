#!/bin/bash
# Запуск Telegram-бота в фоне с nohup, лог и PID

cd "$(dirname "$0")"
nohup poetry run python3 main.py > bot.log 2>&1 &
echo $! > bot.pid      # запомнить PID для последующей остановки
echo "Бот запущен с PID $(cat bot.pid). Лог в bot.log"
