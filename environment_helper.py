import streamlit as st
import os
from typing import Dict, Any

class EnvironmentHelper:
    """Simple helper for managing development and production environments"""
    
    def __init__(self):
        self.current_env = self._detect_environment()
        self.config = self._load_config()
    
    def _detect_environment(self) -> str:
        """Detect environment based on configuration"""
        
        # Method 1: Explicit environment setting in secrets
        if "app" in st.secrets and "current_environment" in st.secrets["app"]:
            return st.secrets["app"]["current_environment"]
        
        # Method 2: Environment variable override
        env_var = os.getenv('STREAMLIT_ENV')
        if env_var:
            return env_var.lower()
        
        # Default to development for safety
        return "development"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration based on current environment"""
        config = {
            "environment": self.current_env,
            "debug_mode": False,
            "google": {}
        }
        
        try:
            # Environment-specific sections (Recommended)
            if ("environments" in st.secrets and 
                self.current_env in st.secrets["environments"]):
                
                env_config = st.secrets["environments"][self.current_env]
                
                # Load Google config
                if "google" in env_config:
                    config["google"] = dict(env_config["google"])
                
                # Load app config
                if "app" in env_config:
                    config.update(env_config["app"])
            
            # Fallback to base configuration
            else:
                if "google" in st.secrets:
                    config["google"] = dict(st.secrets["google"])
                if "app" in st.secrets:
                    config.update(st.secrets["app"])
                    
        except Exception as e:
            st.error(f"Error loading environment configuration: {e}")
            raise
        
        return config
    
    def get_credentials_file(self) -> str:
        """Get Google credentials file path"""
        return self.config["google"].get("credentials_file", "")
    
    def get_spreadsheet_id(self) -> str:
        """Get Google Sheets ID"""
        return self.config["google"].get("spreadsheet_id", "")
    
    def get_drive_folder_id(self) -> str:
        """Get Google Drive folder ID"""
        return self.config["google"].get("drive_folder_id", "")
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.config.get("debug_mode", False)
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.current_env == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.current_env == "development"
    
    def validate_required_secrets(self, required_secrets: list) -> bool:
        """Validate that all required secrets are present"""
        missing_secrets = []
        
        for secret_key in required_secrets:
            keys = secret_key.split(".")
            current = self.config
            
            try:
                for k in keys:
                    current = current[k]
                if not current:
                    missing_secrets.append(secret_key)
            except (KeyError, TypeError):
                missing_secrets.append(secret_key)
        
        if missing_secrets:
            st.error(f"Missing required secrets for {self.current_env} environment:")
            for secret in missing_secrets:
                st.error(f"  - {secret}")
            st.error("Please check your .streamlit/secrets.toml file.")
            return False
        
        return True
    
    def show_environment_info(self, show_in_sidebar: bool = True):
        """Display current environment information"""
        container = st.sidebar if show_in_sidebar else st
        
        if self.is_production():
            container.success(f"🚀 PRODUCTION")
        else:
            container.warning(f"🧪 DEVELOPMENT")

# Cached instance for reuse
@st.cache_resource
def get_environment_helper() -> EnvironmentHelper:
    """Get cached environment helper instance"""
    return EnvironmentHelper() 