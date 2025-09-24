#!/bin/bash
# Остановка процесса по PID из файла bot.pid

cd "$(dirname "$0")"
if [[ -f bot.pid ]]; then
    kill $(cat bot.pid) && echo "Бот остановлен" || echo "Процесс не найден"
    rm -f bot.pid
else
    echo "Файл bot.pid не найден. Возможно, бот уже остановлен."
fi
