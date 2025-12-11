#!/usr/bin/env python3
"""
Rutas de búsqueda y análisis integrado
"""
import json
import socket
import time
import logging
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from config import Config

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


@search_bp.route('/analyze', methods=['POST', 'OPTIONS'])
def search_analyze():
    """Workflow completo: SerpStack → DNS → Cloudflare → IP-API → Censys"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response, 200
    
    try:
        start_time = time.time()
        data = request.json or {}

        # Validar query
        query = data.get('query')
        if not query:
            return jsonify({"status": "error", "error": "Parámetro 'query' requerido"}), 400

        num_results = data.get('num_results', 5)
        analyze_top = data.get('analyze_top', 3)
        include_censys = data.get('include_censys', True)
        ipapi_lang = data.get('ipapi_lang', 'en')

        registry = current_app.config['PROVIDER_REGISTRY']
        crypto = current_app.config['CRYPTO_MANAGER']

        # PASO 1: Buscar con SerpStack
        logging.info(f"🔍 Buscando '{query}' en Google...")
        serpstack = registry.get_provider('serpstack')
        
        if not serpstack:
            return jsonify({"status": "error", "error": "SerpStack no disponible"}), 500

        serp_result = serpstack.extract_domains(query=query, num=num_results)

        if not serp_result.get('success'):
            return jsonify({
                "status": "error",
                "step": "serpstack",
                "error": serp_result.get('error')
            }), 500

        domains_found = serp_result.get('domains', [])

        if not domains_found:
            execution_time = time.time() - start_time
            return jsonify({
                "query": query,
                "results": [],
                "total_results": 0,
                "execution_time": execution_time
            }), 200

        # PASO 2: Analizar dominios
        logging.info(f"🔬 Analizando top {analyze_top} dominios...")
        analyzed_domains = []

        cloudflare = registry.get_provider('cloudflare')
        ipapi = registry.get_provider('ipapi')
        censys = registry.get_provider('censys')

        for idx, domain_info in enumerate(domains_found[:analyze_top], 1):
            domain = domain_info['domain']
            logging.info(f"  [{idx}/{analyze_top}] Analizando {domain}")

            domain_analysis = {
                "domain": domain,
                "title": domain_info.get('title', ''),
                "position": domain_info.get('first_seen_position')
            }

            try:
                # DNS Resolution
                ip = socket.gethostbyname(domain)
                domain_analysis['ip'] = ip
                domain_analysis['dns_resolved'] = True

                # IP-API Geolocation
                ipapi_result = ipapi.lookup(ip=ip, lang=ipapi_lang)
                if ipapi_result.get('success'):
                    geo_data = ipapi_result['data']
                    domain_analysis.update({
                        'geolocation': {
                            "country": geo_data.get('country'),
                            "city": geo_data.get('city'),
                            "isp": geo_data.get('isp'),
                            "lat": geo_data.get('lat'),
                            "lon": geo_data.get('lon')
                        },
                        'country': geo_data.get('country'),
                        'city': geo_data.get('city'),
                        'isp': geo_data.get('isp')
                    })

                # Censys Analysis (opcional)
                if include_censys and censys:
                    import os
                    if os.getenv('CENSYS_API_TOKEN'):
                        censys_result = censys.get_host_summary(ip)
                        if censys_result.get('success'):
                            censys_data = censys_result['data']
                            domain_analysis.update({
                                'censys': {
                                    "ports": censys_data.get('ports', []),
                                    "services_count": len(censys_data.get('services', []))
                                },
                                'open_ports': censys_data.get('ports', []),
                                'services_count': len(censys_data.get('services', []))
                            })

            except socket.gaierror:
                domain_analysis.update({
                    'ip': None,
                    'dns_resolved': False,
                    'error': 'No se pudo resolver DNS'
                })
            except Exception as e:
                domain_analysis['error'] = str(e)
                logging.error(f"  Error: {e}")

            analyzed_domains.append(domain_analysis)

        execution_time = time.time() - start_time

        response_data = {
            "query": query,
            "results": analyzed_domains,
            "total_results": len(analyzed_domains),
            "execution_time": execution_time
        }

        # Guardar resultados encriptados
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c if c.isalnum() else "_" for c in query)[:50]

            encrypted_data = crypto.encrypt_data(response_data)
            sha256_hash = crypto.create_sha256_hash(response_data)

            encrypted_file = Config.OUTPUT_DIR / f"search_{safe_query}_{timestamp}_encrypted.json"
            with open(encrypted_file, 'w') as f:
                json.dump({
                    "encrypted_data": encrypted_data,
                    "sha256_hash": sha256_hash,
                    "timestamp": timestamp
                }, f, indent=2)

            logging.info(f"✅ Resultados guardados: {encrypted_file}")
        except Exception as save_error:
            logging.warning(f"⚠️  Error al guardar: {save_error}")

        return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"❌ Error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500
