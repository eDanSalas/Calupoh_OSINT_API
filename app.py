#!/usr/bin/env python3
"""
Secure Data Provider API - Aplicación Principal
Versión 4.0.0 - Refactorizada
"""
import os
import logging
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth

from config import Config, DevelopmentConfig
from services import CryptoManager, UserManager
from utils import ProviderRegistry
from routes import main_bp, auth_bp, providers_bp, search_bp

# Importar providers
from providers.cloudflare import CloudflareProvider
from providers.censys import CensysProvider
from providers.other_providers import SerpStackProvider, IPAPIProvider, PeeringDBProvider


def create_app(config_class=DevelopmentConfig):
    """
    Factory function para crear la aplicación Flask
    
    Args:
        config_class: Clase de configuración a usar
        
    Returns:
        Instancia de la aplicación Flask configurada
    """
    print("="*70)
    print("  Inicializando Secure Data Provider API v4.0.0")
    print("="*70)
    
    # Crear aplicación Flask
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar configuración
    Config.init_app()
    
    # Configurar CORS
    CORS(app, resources={
        r"/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": Config.CORS_METHODS,
            "allow_headers": Config.CORS_ALLOW_HEADERS
        }
    })
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Inicializar extensiones
    bcrypt = Bcrypt(app)
    jwt = JWTManager(app)
    
    # Configurar OAuth (Google)
    oauth = OAuth(app)
    print("🔐 Configurando Google OAuth...", flush=True)
    google = oauth.register(
        name='google',
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )
    print("✅ Google OAuth configurado", flush=True)
    
    # Inicializar servicios
    print("🔐 Inicializando CryptoManager...", flush=True)
    crypto = CryptoManager(Config.OUTPUT_DIR)
    
    print("👤 Inicializando UserManager...", flush=True)
    user_manager = UserManager(crypto, bcrypt)
    
    # Inicializar registro de providers
    print("📦 Registrando providers...", flush=True)
    registry = ProviderRegistry()
    registry.register(SerpStackProvider())
    registry.register(CloudflareProvider())
    registry.register(IPAPIProvider())
    registry.register(CensysProvider())
    registry.register(PeeringDBProvider())
    print(f"✅ {len(registry.providers)} providers registrados", flush=True)
    
    # Almacenar en configuración de la app
    app.config['CRYPTO_MANAGER'] = crypto
    app.config['USER_MANAGER'] = user_manager
    app.config['PROVIDER_REGISTRY'] = registry
    app.config['GOOGLE_OAUTH'] = google
    
    # Middleware para logging
    @app.before_request
    def log_request_info():
        if request.path.startswith('/api/'):
            logging.info('='*70)
            logging.info(f'🌐 {request.method} {request.path}')
            logging.info(f'📍 From: {request.remote_addr}')
            if request.method == 'POST' and request.json:
                logging.info(f'📝 Body: {request.json}')
            logging.info('='*70)
    
    # Registrar blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(providers_bp)
    app.register_blueprint(search_bp)
    
    print("="*70)
    print("  ✅ Aplicación inicializada correctamente")
    print(f"  📡 Providers: {list(registry.providers.keys())}")
    print(f"  🔍 Endpoint principal: POST /api/search/analyze")
    print("="*70)
    
    return app


def main():
    """Punto de entrada principal"""
    # Configurar para desarrollo local
    os.environ.setdefault('OAUTHLIB_INSECURE_TRANSPORT', '1')
    
    # Crear y ejecutar aplicación
    app = create_app()
    
    logging.info("🚀 Iniciando servidor Flask...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )


if __name__ == '__main__':
    main()
