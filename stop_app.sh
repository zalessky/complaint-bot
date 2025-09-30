#!/bin/bash
echo "🛑 Остановка Городской помощник..."

if [ -f logs/backend.pid ]; then
    kill $(cat logs/backend.pid) 2>/dev/null
    rm logs/backend.pid
    echo "✅ Backend остановлен"
fi

if [ -f logs/bot.pid ]; then
    kill $(cat logs/bot.pid) 2>/dev/null
    rm logs/bot.pid
    echo "✅ Bot остановлен"
fi

echo "✅ Приложение остановлено"
