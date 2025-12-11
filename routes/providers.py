#!/usr/bin/env python3
"""
Rutas para consultas a providers
"""
import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from config import Config

providers_bp = Blueprint('providers', __name__, url_prefix='/api')


@providers_bp.route('/providers', methods=['GET'])
def list_providers():
    """Lista todos los providers disponibles"""
    from flask import current_app
    
    registry = current_app.config['PROVIDER_REGISTRY']
    providers_info = registry.list_providers()
    
    return jsonify({
        "status": "success",
        "total_providers": len(providers_info),
        "providers": providers_info
    }), 200


@providers_bp.route('/query', methods=['POST'])
def query_encrypted():
    """Consulta a provider con respuesta encriptada"""
    from flask import current_app
    
    try:
        registry = current_app.config['PROVIDER_REGISTRY']
        crypto = current_app.config['CRYPTO_MANAGER']
        data = request.json

        if not data:
            return jsonify({"error": "Body JSON requerido"}), 400

        provider_name = data.get('provider')
        params = data.get('params', {})

        if not provider_name:
            return jsonify({
                "error": "Campo 'provider' requerido",
                "available_providers": list(registry.providers.keys())
            }), 400

        provider = registry.get_provider(provider_name)
        if not provider:
            return jsonify({
                "error": f"Provider '{provider_name}' no encontrado",
                "available_providers": list(registry.providers.keys())
            }), 404

        # Obtener datos del provider
        result_data = provider.fetch_data(params)

        response_data = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "provider": provider_name,
            "request_params": params,
            "data": result_data
        }

        # Encriptar respuesta
        encrypted_data = crypto.encrypt_data(response_data)
        sha256_hash = crypto.create_sha256_hash(response_data)

        encrypted_response = {
            "encrypted_data": encrypted_data,
            "sha256_hash": sha256_hash,
            "public_key_file": "public_key.pem",
            "note": "Use the private key to decrypt the data",
            "provider": provider_name
        }

        # Guardar en archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Config.OUTPUT_DIR / f"query_{provider_name}_{timestamp}.json"

        import json
        with open(output_file, 'w') as f:
            json.dump({
                "encrypted": encrypted_response,
                "plain": response_data
            }, f, indent=2, ensure_ascii=False)

        logging.info(f"✅ Consulta guardada: {output_file}")

        return jsonify(encrypted_response), 200

    except Exception as e:
        logging.error(f"Error en query_encrypted: {e}")
        return jsonify({"error": str(e)}), 500


@providers_bp.route('/query/plain', methods=['POST'])
def query_plain():
    """Consulta a provider sin encriptación"""
    from flask import current_app
    
    try:
        registry = current_app.config['PROVIDER_REGISTRY']
        data = request.json

        if not data:
            return jsonify({"error": "Body JSON requerido"}), 400

        provider_name = data.get('provider')
        params = data.get('params', {})

        if not provider_name:
            return jsonify({
                "error": "Campo 'provider' requerido",
                "available_providers": list(registry.providers.keys())
            }), 400

        provider = registry.get_provider(provider_name)
        if not provider:
            return jsonify({
                "error": f"Provider '{provider_name}' no encontrado",
                "available_providers": list(registry.providers.keys())
            }), 404

        result_data = provider.fetch_data(params)

        response_data = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "provider": provider_name,
            "request_params": params,
            "data": result_data
        }

        return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"Error en query_plain: {e}")
        return jsonify({"error": str(e)}), 500
