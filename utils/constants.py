from enum import Enum
from typing import Dict

CATEGORIES = {
    "transport": {
        "name": "🚌 Транспорт и остановки",
        "subcategories": {
            1: {"name": "😡 Поведение водителя (грубость, курение)", "route_instead_of_address": True},
            2: {"name": "🚦 Нарушение ПДД водителем", "route_instead_of_address": True},
            3: {"name": "🧹 Грязный салон", "route_instead_of_address": True},
            4: {"name": "🛠️ Неисправность транспортного средства", "route_instead_of_address": True},
            5: {"name": "⏰ Нарушение графика/игнорирование остановки", "route_instead_of_address": True},
            6: {"name": "🚫 Отказ в приеме карты/проездного/льготы", "route_instead_of_address": True},
            7: {"name": "♿ Трудности при посадке", "route_instead_of_address": True},
            8: {"name": "🏚️ Нет павильона", "geo_required": True},
            9: {"name": "🪣 Павильон грязный/сломанный", "geo_required": True},
            10: {"name": "🪧 Нет названия остановки", "geo_required": True},
            11: {"name": "🧭 Неверный маршрут/самовольный объезд", "route_instead_of_address": True},
            12: {"name": "🔍 Другое"}
        }
    },
    "waste": {
        "name": "🗑️ Мусор/контейнеры",
        "subcategories": {
            1: {"name": "♻️ Переполненные контейнеры", "geo_required": True},
            2: {"name": "🔥 Стихийная свалка", "geo_required": True},
            3: {"name": "🛻 Сброс мусора с транспорта", "geo_required": True, "photo_required": True},
            4: {"name": "🔨 Поврежденные контейнеры"},
            5: {"name": "🤢 Грязная площадка/нужна уборка"},
            6: {"name": "🌫️ Нужна помывка контейнеров"},
            7: {"name": "🐀 Дератизация/дезинсекция"},
            8: {"name": "🚮 Нет контейнера"},
            9: {"name": "🗓️ Несвоевременный вывоз/пропуск графика"},
            10: {"name": "🔍 Другое"}
        }
    },
    "roads": {
        "name": "🚧 Дороги и ямы",
        "subcategories": {
            1: {"name": "🕳️ Ямы на дорогах/тротуарах", "geo_required": True},
            2: {"name": "🧱 Разрушенное покрытие", "geo_required": True},
            3: {"name": "❄️ Неубранный снег/наледь", "geo_required": True},
            4: {"name": "🚥 Светофор не работает", "geo_required": True},
            5: {"name": "🚫 Знак отсутствует/сломался", "geo_required": True},
            6: {"name": "📏 Нет разметки/стерлась", "geo_required": True},
            7: {"name": "💧 Глубокие лужи/нужна откачка", "geo_required": True},
            8: {"name": "🧱 Бордюры/поребрики разрушены", "geo_required": True},
            9: {"name": "🧑‍🦽 Пандусы/тактильная плитка отсутствуют", "geo_required": True},
            10: {"name": "🕯️ Уличное освещение не работает", "geo_required": True},
            11: {"name": "🕹️ Сломаны дорожные ограждения", "geo_required": True},
            12: {"name": "🐢 Пробки из‑за организации движения", "geo_required": True},
            13: {"name": "🔍 Другое"}
        }
    },
    "plants": {
        "name": "🌳 Озеленение/вырубка",
        "subcategories": {
            1: {"name": "🪓 Незаконная вырубка", "geo_required": True},
            2: {"name": "🌿 Заросли/сорняки — нужен покос", "geo_required": True},
            3: {"name": "🌲 Кусты/деревья закрывают обзор", "geo_required": True},
            4: {"name": "🥀 Посадки в плохом состоянии", "geo_required": True},
            5: {"name": "⚠️ Сухостой/риск падения", "geo_required": True},
            6: {"name": "💧 Нужен полив", "geo_required": True},
            7: {"name": "🐛 Вредители/болезни", "geo_required": True},
            8: {"name": "🌷 Требуются новые посадки", "geo_required": True},
            9: {"name": "♻️ Листва/ветки не вывезены", "geo_required": True},
            10: {"name": "🔍 Другое"}
        }
    },
    "utilities": {
        "name": "🔧 ЖКХ",
        "subcategories": {
            1: {"name": "💦 Прорыв трубы", "geo_required": True},
            2: {"name": "🕳️ Открытый люк", "geo_required": True},
            3: {"name": "💡 Не горит уличный фонарь", "geo_required": True},
            4: {"name": "🔌 Обрыв/искрение проводов", "geo_required": True},
            5: {"name": "🧯 Пожарная безопасность нарушена", "geo_required": True},
            6: {"name": "Протечка канализации", "geo_required": True},
            7: {"name": "🔍 Другое"}
        }
    },
    "landscaping": {
        "name": "🏞️ Благоустройство дворов/парков/скверов",
        "subcategories": {
            1: {"name": "🪑 Сломаны лавочки/урны", "geo_required": True},
            2: {"name": "🛝 Детская площадка повреждена/опасна", "geo_required": True},
            3: {"name": "🚴 Дефекты велодорожек/скейт‑зон", "geo_required": True},
            4: {"name": "🚻 Туалеты не работают/грязные", "geo_required": True},
            5: {"name": "🧼 Территория грязная/нужен субботник", "geo_required": True},
            6: {"name": "🧊 Гололед на прогулочных зонах", "geo_required": True},
            7: {"name": "🔍 Другое"}
        }
    },
    "parking": {
        "name": "🅿️ Парковки и эвакуация",
        "subcategories": {
            1: {"name": "🅿️ Нелегальная парковка/блокировка", "geo_required": True},
            2: {"name": "🚫 Парковка на газоне/тротуаре", "geo_required": True},
            3: {"name": "🚓 Нужен эвакуатор", "geo_required": True},
            4: {"name": "💳 Не работает оплата/паркомат", "geo_required": True},
            5: {"name": "🪧 Нет знаков/разметки парковки", "geo_required": True},
            6: {"name": "Брошенный/бесхозный транспорт", "geo_required": True},
            7: {"name": "🔍 Другое"}
        }
    },
    "construction": {
        "name": "🏗️ Стройка и шум",
        "subcategories": {
            1: {"name": "🔊 Шум ночью/нарушение тишины", "geo_required": True},
            2: {"name": "🧱 Опасный стройобъект/ограждения", "geo_required": True},
            3: {"name": "🧹 Строительный мусор", "geo_required": True},
            4: {"name": "🚧 Перекрытие прохода без схемы", "geo_required": True},
            5: {"name": "Выезд со стройплощадки без мойки колес", "geo_required": True},
            6: {"name": "🔍 Другое"}
        }
    },
    "animals": {
        "name": "🐾 Животные",
        "subcategories": {
            1: {"name": "🐕 Агрессивные/бездомные собаки", "geo_required": True},
            2: {"name": "Мертвое животное", "geo_required": True},
            3: {"name": "🐱 Раненые/потерянные животные", "geo_required": True},
            4: {"name": "💩 Неубранные экскременты", "geo_required": True},
            5: {"name": "🐀 Крысы/мыши во дворе/подвале", "geo_required": True},
            6: {"name": "🔍 Другое"}
        }
    },
    "trade_service": {
        "name": "🏬 Торговля и сервис",
        "subcategories": {
            1: {"name": "🧾 Обвес/обман/отказ выдать чек"},
            2: {"name": "🍗 Несоблюдение санитарии"},
            3: {"name": "🕰️ Торговля в неположенное время"},
            4: {"name": "🏪 Незаконная торговля"},
            5: {"name": "🔊 Уличная реклама/звуки мешают"},
            6: {"name": "🔍 Другое"}
        }
    },
    "water_bodies": {
        "name": "🌊 Водоемы и набережные",
        "subcategories": {
            1: {"name": "🏖️ Загрязнение берега/воды", "geo_required": True},
            2: {"name": "🛶 Опасные/сломанные пирсы/понтоны", "geo_required": True},
            3: {"name": "🚫 Купание запрещено — нет знаков", "geo_required": True},
            4: {"name": "Заросли камыша - требуется покос", "geo_required": True},
            5: {"name": "Сброс вредных веществ в водоем", "geo_required": True},
            6: {"name": "🔍 Другое"}
        }
    },
    "emergency_buildings": {
        "name": "🏚️ Аварийные здания",
        "subcategories": {
            1: {"name": "🧱 Трещины/обрушения", "geo_required": True},
            2: {"name": "🚷 Опасные подъезды/лестницы", "geo_required": True},
            3: {"name": "🪧 Нет предупреждающих табличек", "geo_required": True},
            4: {"name": "🔍 Другое"}
        }
    },
    "navigation_tactility": {
        "name": "🧭 Навигация и тактильность",
        "subcategories": {
            1: {"name": "🔡 Нет адресных табличек/номеров домов", "geo_required": True},
            2: {"name": "🟨 Тактильная плитка повреждена/отсутствует", "geo_required": True},
            3: {"name": "🦽 Нет доступного входа/кнопки вызова", "geo_required": True},
            4: {"name": "Неисправен лифтовой подъемник в подземном переходе", "geo_required": True},
            5: {"name": "🔍 Другое"}
        }
    },
    "feedback": {
        "name": "📢 Обратная связь",
        "subcategories": {
            1: {"name": "💬 Предложение по улучшению"},
            2: {"name": "🗣️ Сообщить об ошибке"}
        }
    },
    "gratitude": {
        "name": "🙏 Благодарность",
        "subcategories": {
            1: {"name": "Общая благодарность"}
        }
    }
}

class ComplaintStatus(Enum):
    NEW = "new"
    IN_WORK = "in_work"
    CLARIFICATION_NEEDED = "clarification_needed"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    CLOSED = "closed"

STATUS_LABEL_RU: Dict[str, str] = {
    "new": "🆕 Новая",
    "in_work": "⏳ В работе",
    "clarification_needed": "❓ Нужны уточнения",
    "resolved": "✅ Решена",
    "rejected": "❌ Отклонена",
    "closed": "📁 Закрыта",
}
