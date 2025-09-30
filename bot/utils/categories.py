import json
from pathlib import Path
from typing import List, Dict, Optional

class CategoriesManager:
    def __init__(self, config_path: str = "config/categories.json"):
        self.config_path = Path(config_path)
        self.data = self._load_config()
    
    def _load_config(self) -> dict:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_categories(self) -> List[str]:
        return list(self.data['categories'].keys())
    
    def get_subcategories(self, category: str) -> List[str]:
        return self.data['categories'].get(category, {}).get('subcategories', [])
    
    def get_category_fields(self, category: str, subcategory: Optional[str] = None) -> List[str]:
        """
        Возвращает поля для категории.
        Если есть fields_by_subcategory - использует их, иначе общие fields
        """
        cat_data = self.data['categories'].get(category, {})
        
        # Проверяем есть ли специфичные поля для подкатегории
        if subcategory and 'fields_by_subcategory' in cat_data:
            return cat_data['fields_by_subcategory'].get(subcategory, cat_data.get('fields', []))
        
        return cat_data.get('fields', [])
    
    def get_field_definition(self, field_name: str) -> Optional[Dict]:
        return self.data['field_definitions'].get(field_name)
    
    def get_field_type(self, field_name: str) -> str:
        field_def = self.get_field_definition(field_name)
        return field_def.get('type', 'text') if field_def else 'text'
    
    def get_field_prompt(self, field_name: str) -> str:
        field_def = self.get_field_definition(field_name)
        return field_def.get('prompt', f'Введите {field_name}:') if field_def else f'Введите {field_name}:'
    
    def is_field_required(self, field_name: str) -> bool:
        field_def = self.get_field_definition(field_name)
        return field_def.get('required', False) if field_def else False

categories_manager = CategoriesManager()
