import json
from pathlib import Path
from typing import Dict, List, Optional

class CategoriesManager:
    """Менеджер категорий жалоб с поддержкой гибких полей"""
    
    def __init__(self, config_path: str = "config/categories.json"):
        self.config_path = Path(config_path)
        self._data = None
    
    def load_data(self) -> Dict:
        """Загружает все данные из JSON файла"""
        if self._data is None:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except FileNotFoundError:
                self._data = self._get_default_data()
        return self._data
    
    def get_categories(self) -> List[str]:
        """Возвращает список названий категорий"""
        data = self.load_data()
        return list(data.get('categories', {}).keys())
    
    def get_subcategories(self, category: str) -> List[str]:
        """Возвращает подкатегории для указанной категории"""
        data = self.load_data()
        categories = data.get('categories', {})
        if category in categories:
            return categories[category].get('subcategories', [])
        return []
    
    def get_category_description(self, category: str) -> str:
        """Возвращает описание категории"""
        data = self.load_data()
        categories = data.get('categories', {})
        if category in categories:
            return categories[category].get('description', '')
        return ''
    
    def get_category_fields(self, category: str) -> List[str]:
        """Возвращает список полей для категории"""
        data = self.load_data()
        categories = data.get('categories', {})
        if category in categories:
            return categories[category].get('fields', ['description'])
        return ['description']
    
    def get_field_definition(self, field_name: str) -> Optional[Dict]:
        """Возвращает определение поля"""
        data = self.load_data()
        field_defs = data.get('field_definitions', {})
        return field_defs.get(field_name)
    
    def get_field_prompt(self, field_name: str) -> str:
        """Возвращает текст запроса для поля"""
        field_def = self.get_field_definition(field_name)
        if field_def:
            return field_def.get('prompt', f'Введите {field_name}:')
        return f'Введите {field_name}:'
    
    def is_field_required(self, field_name: str) -> bool:
        """Проверяет, обязательно ли поле"""
        field_def = self.get_field_definition(field_name)
        if field_def:
            return field_def.get('required', False)
        return False
    
    def get_field_type(self, field_name: str) -> str:
        """Возвращает тип поля"""
        field_def = self.get_field_definition(field_name)
        if field_def:
            return field_def.get('type', 'text')
        return 'text'
    
    def save_data(self, data: Dict):
        """Сохраняет данные в JSON файл"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._data = data
    
    def _get_default_data(self) -> Dict:
        """Базовые данные по умолчанию"""
        return {
            "categories": {},
            "field_definitions": {}
        }

# Глобальный экземпляр менеджера
categories_manager = CategoriesManager()
