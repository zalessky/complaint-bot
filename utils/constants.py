from enum import Enum

CATEGORIES = {
    "transport": { "name": "🚌 Общественный транспорт", "subcategories": {
        1: {"name": "Поведение водителя (грубость, курение)"}, 2: {"name": "Нарушение ПДД водителем"},
        3: {"name": "Техническое состояние (грязь, поломка)"}, 4: {"name": "Нарушение графика / игнорирование остановки"},
        5: {"name": "Отказ в льготном проезде / приеме оплаты"}, 6: {"name": "Другое"},
    }},
    "waste": { "name": "🗑️ Мусор и площадки ТКО", "subcategories": {
        1: {"name": "Переполненные контейнеры", "geo_required": True}, 2: {"name": "Стихийная свалка", "geo_required": True},
        3: {"name": "Сброс мусора с ТС", "geo_required": True, "photo_required": True}, 4: {"name": "Поврежденные контейнеры"},
        5: {"name": "Грязная контейнерная площадка"}, 6: {"name": "Другое"},
    }},
    "landscaping": { "name": "🌳 Благоустройство", "subcategories": {
        1: {"name": "Ямы на дорогах / тротуарах", "geo_required": True}, 2: {"name": "Неработающее освещение", "geo_required": True},
        3: {"name": "Сломанные скамейки / урны / площадки"}, 4: {"name": "Неубранный снег / наледь"},
        5: {"name": "Брошенный автомобиль"}, 6: {"name": "Другое"},
    }},
    "utilities": { "name": "🔧 ЖКХ (Коммунальные услуги)", "subcategories": {
        1: {"name": "Прорыв трубы / открытый люк", "geo_required": True}, 2: {"name": "Отсутствие отопления / воды (аварийное)"},
        3: {"name": "Слабый напор воды"}, 4: {"name": "Проблемы с электроснабжением"}, 5: {"name": "Другое"},
    }}
}

class ComplaintStatus(Enum):
    NEW = "new"; IN_WORK = "in_work"; CLARIFICATION_NEEDED = "clarification_needed"; RESOLVED = "resolved"; MEASURES_TAKEN = "measures_taken"; NOT_CONFIRMED = "not_confirmed"; REJECTED = "rejected"
