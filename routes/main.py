#!/usr/bin/env python3
"""
Rutas principales de la API
"""
from flask import Blueprint, jsonify, send_file
from datetime import datetime
from config import Config

main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET'])
def index():
    """Endpoint raíz con información del servicio"""
    return jsonify({
        "service": "Secure Data Provider API",
        "version": Config.VERSION,
        "description": "API REST con búsqueda SERP, análisis de IPs y salida encriptada",
        "endpoints": [
            {"method": "POST", "path": "/api/search/analyze", "description": "🌟 Buscar → Analizar → Reportar"},
            {"method": "GET", "path": "/api/providers", "description": "Listar providers"},
            {"method": "POST", "path": "/api/query", "description": "Consulta encriptada"},
            {"method": "POST", "path": "/api/query/plain", "description": "Consulta sin encriptar"},
            {"method": "GET", "path": "/api/keys/public", "description": "Descargar llave pública"},
            {"method": "GET", "path": "/api/health", "description": "Estado de salud"}
        ],
        "workflow": "SerpStack → DNS → Cloudflare → IP-API → Censys"
    }), 200


@main_bp.route('/api/health', methods=['GET'])
def health_check():
    """Verifica el estado de salud del servicio"""
    from flask import current_app
    
    registry = current_app.config['PROVIDER_REGISTRY']
    
    return jsonify({
        "status": "healthy",
        "service": "Secure Data Provider API",
        "version": Config.VERSION,
        "timestamp": datetime.now().isoformat(),
        "providers_available": len(registry.providers),
        "providers": list(registry.providers.keys()),
        "encryption": "RSA-2048 + SHA-256"
    }), 200


@main_bp.route('/api/keys/public', methods=['GET'])
def get_public_key():
    """Descarga la llave pública RSA"""
    try:
        key_path = Config.OUTPUT_DIR / "public_key.pem"
        if key_path.exists():
            return send_file(key_path, as_attachment=True)
        return jsonify({"error": "Public key not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/keys/private', methods=['GET'])
def get_private_key():
    """Descarga la llave privada RSA"""
    try:
        key_path = Config.OUTPUT_DIR / "private_key.pem"
        if key_path.exists():
            return send_file(key_path, as_attachment=True)
        return jsonify({"error": "Private key not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
