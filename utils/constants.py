from enum import Enum
from typing import Dict

CATEGORIES = {
    "transport": {
        "name": "🚌 Транспорт и остановки",
        "subcategories": {
            1: {"name": "😡 Поведение водителя (грубость, курение)"},
            2: {"name": "🚦 Нарушение ПДД водителем"},
            3: {"name": "🧹 Грязь/поломка транспорта"},
            4: {"name": "⏰ Нарушение графика / игнорирование остановки"},
            5: {"name": "🚫 Отказ в льготном проезде / оплате"},
            6: {"name": "🏚️ Нет остановочного павильона", "geo_required": True},
            7: {"name": "🪣 Павильон грязный", "geo_required": True},
            8: {"name": "🪧 Нет вывески с названием остановки", "geo_required": True},
            9: {"name": "🔍 Другое"},
        }
    },
    "waste": {
        "name": "🗑️ Мусор/контейнеры",
        "subcategories": {
            1: {"name": "♻️ Переполненные контейнеры", "geo_required": True},
            2: {"name": "🔥 Стихийная свалка", "geo_required": True},
            3: {"name": "🛻 Сброс мусора с ТС", "geo_required": True, "photo_required": True},
            4: {"name": "🔨 Поврежденные контейнеры"},
            5: {"name": "🤢 Грязная площадка"},
            6: {"name": "🌫️ Контейнер не моется годами"},
            7: {"name": "🔍 Другое"},
        }
    },
    "roads": {
        "name": "🚧 Дороги и ямы",
        "subcategories": {
            1: {"name": "🕳️ Ямы на дорогах/тротуарах", "geo_required": True},
            2: {"name": "🧱 Разбитое покрытие", "geo_required": True},
            3: {"name": "❄️ Неубранный снег/наледь", "geo_required": True},
            4: {"name": "🔍 Другое"},
        }
    },
    "plants": {
        "name": "🌳 Озеленение/вырубка",
        "subcategories": {
            1: {"name": "🪓 Вырубка деревьев", "geo_required": True},
            2: {"name": "🌿 Заросли/сорняки", "geo_required": True},
            3: {"name": "🌲 Кусты/деревья мешают обзору", "geo_required": True},
            4: {"name": "🥀 Посадки в плохом состоянии", "geo_required": True},
            5: {"name": "🔍 Другое"},
        }
    },
    "utilities": {
        "name": "🔧 ЖКХ",
        "subcategories": {
            1: {"name": "🕳️ Прорыв трубы / открытый люк", "geo_required": True},
            2: {"name": "🥶 Нет отопления / воды"},
            3: {"name": "🚿 Слабый напор воды"},
            4: {"name": "💡 Электроснабжение"},
            5: {"name": "🔍 Другое"},
        }
    }
}

class ComplaintStatus(Enum):
    NEW = "new"
    IN_WORK = "in_work"
    CLARIFICATION_NEEDED = "clarification_needed"
    RESOLVED = "resolved"
    MEASURES_TAKEN = "measures_taken"
    NOT_CONFIRMED = "not_confirmed"
    REJECTED = "rejected"

# Русские подписи статусов для UI
STATUS_LABEL_RU: Dict[str, str] = {
    "new": "Новое",
    "in_work": "В работе",
    "clarification_needed": "Требует уточнения",
    "resolved": "Решено",
    "measures_taken": "Приняты меры",
    "not_confirmed": "Не подтвердилось",
    "rejected": "Отклонено",
}

