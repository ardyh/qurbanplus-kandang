import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

class ConfigHelper:
    def __init__(self):
        self.config_dir = "config"
        self._vendors = None
        self._animals = None
        self._sheets = None
        self._ui_labels = None
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {filepath} not found")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}")
    
    @property
    def vendors(self) -> Dict[str, List[str]]:
        """Get vendor configurations"""
        if self._vendors is None:
            self._vendors = self._load_json("vendors.json")
        return self._vendors
    
    @property
    def animals(self) -> Dict[str, List[str]]:
        """Get animal configurations"""
        if self._animals is None:
            self._animals = self._load_json("animals.json")
        return self._animals
    
    @property
    def sheets(self) -> Dict[str, Any]:
        """Get sheet configurations"""
        if self._sheets is None:
            self._sheets = self._load_json("sheets.json")
        return self._sheets
    
    @property
    def ui_labels(self) -> Dict[str, Any]:
        """Get UI label configurations"""
        if self._ui_labels is None:
            self._ui_labels = self._load_json("ui_labels.json")
        return self._ui_labels
    
    # Convenience methods for commonly used configs
    def get_sheep_vendors(self) -> List[str]:
        return self.vendors["sheep_vendors"]
    
    def get_cow_vendors(self) -> List[str]:
        return self.vendors["cow_vendors"]
    
    def get_animal_types(self) -> List[str]:
        return self.animals["animal_types"]
    
    def get_sheep_categories(self) -> List[str]:
        return self.animals["sheep_categories"]
    
    def get_cow_categories(self) -> List[str]:
        return self.animals["cow_categories"]
    
    def get_sheet_name(self, sheet_type: str) -> str:
        """Get sheet name by type (inbound/outbound)"""
        return self.sheets["sheet_names"][sheet_type]
    
    def get_hari_h_date(self, form_type: str = "inbound") -> datetime:
        """Get Hari H date for the specified form type"""
        if form_type == "outbound":
            date_str = self.sheets["date_config"]["hari_h_outbound"]
        else:
            date_str = self.sheets["date_config"]["hari_h"]
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    
    def get_hari_options(self, form_type: str = "inbound") -> Dict[str, datetime]:
        """Generate Hari options based on Hari H"""
        hari_h = self.get_hari_h_date(form_type)
        return {
            "H-4": hari_h - timedelta(days=4),
            "H-3": hari_h - timedelta(days=3),
            "H-1": hari_h - timedelta(days=1),
            "H": hari_h,
            "H+1": hari_h + timedelta(days=1),
            "H+2": hari_h + timedelta(days=2)
        }
    
    def get_form_labels(self, form_type: str) -> Dict[str, Any]:
        """Get form labels for the specified form type"""
        return self.ui_labels["forms"][form_type]
    
    def get_message(self, message_type: str) -> str:
        """Get UI message by type"""
        return self.ui_labels["messages"][message_type] 