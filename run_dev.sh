#!/bin/bash
echo "🚀 Запуск Городской помощник v0.8.1 (режим отладки)"
echo ""
echo "Команды tmux:"
echo "  Ctrl+B → стрелки - переключение"
echo "  Ctrl+B → [ - режим копирования (q для выхода)"
echo "  Ctrl+B → D - отключиться"
echo ""

bash stop_app.sh 2>/dev/null
sleep 2

if ! command -v tmux &> /dev/null; then
    apt-get install -y tmux
fi

# Создаем сессию
tmux new-session -d -s citybot

# Разделяем ВЕРТИКАЛЬНО (один над другим)
tmux split-window -v -t citybot

# Верхняя панель - Backend
tmux send-keys -t citybot:0.0 "cd $(pwd) && echo '🔧 BACKEND API' && echo '' && PYTHONPATH=. poetry run python backend/main.py" C-m

# Нижняя панель - Bot  
tmux send-keys -t citybot:0.1 "cd $(pwd) && echo '🤖 TELEGRAM BOT' && echo '' && PYTHONPATH=. poetry run python run_bot.py" C-m

# Подключаемся
tmux attach -t citybot
