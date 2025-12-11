#!/usr/bin/env python3
"""
Configuración centralizada de la aplicación
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'una-clave-muy-secreta-y-aleatoria-12345')
    DEBUG = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super-secret-key-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hora
    
    # JSON
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # CORS
    CORS_ORIGINS = "*"
    CORS_METHODS = ["GET", "POST", "OPTIONS"]
    CORS_ALLOW_HEADERS = "*"
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    FRONTEND_URL = "http://192.168.137.1.nip.io:4200"
    
    # Directorios
    BASE_DIR = Path(__file__).parent
    OUTPUT_DIR = BASE_DIR / "shared_data"
    
    # APIs Externas
    CENSYS_API_TOKEN = os.getenv('CENSYS_API_TOKEN')
    CENSYS_API_ID = os.getenv('CENSYS_API_ID')
    CENSYS_API_SECRET = os.getenv('CENSYS_API_SECRET')
    SERPSTACK_API_KEY = os.getenv('SERPSTACK_API_KEY')
    
    # Replicación
    SECONDARY_SERVER_IP = "192.168.1.102"
    REPLICATION_USER = "hadoop"
    REMOTE_DEST_DIR = "/mnt/shared_data"
    HADOOP_BIN = "hadoop"
    
    # Aplicación
    VERSION = "4.0.0"
    
    @classmethod
    def init_app(cls):
        """Inicializa configuraciones de la aplicación"""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio de salida creado: {cls.OUTPUT_DIR.absolute()}")


class DevelopmentConfig(Config):
    """Configuración de desarrollo"""
    DEBUG = True


class ProductionConfig(Config):
    """Configuración de producción"""
    DEBUG = False


# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
