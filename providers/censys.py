#!/usr/bin/env python3
"""
Provider para Censys Platform API v3 - Global Asset Host (Free tier)
"""
import os
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List
from .base import BaseProvider


class CensysProvider(BaseProvider):
    """Provider para Censys Platform API v3 - Global Asset Host (Free tier)"""

    V3_GLOBAL_ASSET_HOST = "https://api.platform.censys.io/v3/global/asset/host"

    def __init__(self, api_token: str = None):
        """
        Inicializa el provider de Censys Platform API v3

        Args:
            api_token: Token de API de Censys (censys_xxx)
        """
        self.api_version = 'v3'
        self.api_token = api_token or os.getenv('CENSYS_API_TOKEN')

        if self.api_token and self.api_token.startswith('censys_'):
            logging.info("✅ Usando CENSYS_API_TOKEN - Platform API v3")
        else:
            logging.error("❌ CENSYS_API_TOKEN requerido (formato: censys_xxx)")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SecureDataProvider/4.0.0',
            'Accept': 'application/vnd.censys.api.v3.host.v1+json'
        })

        if self.api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}'
            })

    def get_name(self) -> str:
        return "censys"

    def get_version(self) -> str:
        return "2.0.0"

    def get_available_endpoints(self) -> List[Dict[str, str]]:
        """Retorna información sobre los endpoints disponibles"""
        return [
            {
                "type": "view_host",
                "description": "Ver información de un host (GET /v3/global/asset/host/{ip})",
                "requires_credits": False,
                "tier": "Free",
                "url": "https://api.platform.censys.io/v3/global/asset/host/{ip}"
            }
        ]

    def view_host(self, ip: str) -> Dict[str, Any]:
        """
        Ver información de un host usando Global Asset Host endpoint

        Args:
            ip: Dirección IP del host

        Returns:
            Información del host
        """
        if not self.api_token:
            return {
                "success": False,
                "error": "CENSYS_API_TOKEN no configurada"
            }

        url = f"{self.V3_GLOBAL_ASSET_HOST}/{ip}"
        logging.debug(f"🔍 View host: {ip} - URL: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            return {
                "success": True,
                "data": response.json(),
                "status_code": response.status_code
            }

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else None

            if status_code == 403:
                error_msg = "Acceso denegado (403) - Verifica permisos"
            elif status_code == 401:
                error_msg = "Autenticación fallida (401) - Verifica tu token"
            elif status_code == 404:
                error_msg = f"Host {ip} no encontrado (404)"
            else:
                error_msg = str(e)

            logging.error(f"❌ Error {status_code}: {error_msg}")

            return {
                "success": False,
                "error": error_msg,
                "status_code": status_code
            }

        except requests.RequestException as e:
            logging.error(f"❌ Request error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_host_summary(self, ip: str) -> Dict[str, Any]:
        """
        Obtener resumen de un host

        Args:
            ip: Dirección IP

        Returns:
            Resumen con información clave extraída
        """
        result = self.view_host(ip)

        if not result.get('success'):
            return result

        api_data = result.get('data', {})
        host_data = api_data.get('result', {}).get('resource', {})

        if not host_data:
            return {
                "success": False,
                "error": f"Host {ip} no encontrado en Censys"
            }

        services = host_data.get('services', [])
        ports = [s.get('port') for s in services if s.get('port')]

        location = host_data.get('location', {})
        asn_info = host_data.get('autonomous_system', {})
        dns_data = host_data.get('dns', {})
        dns_names = dns_data.get('names', [])

        summary = {
            "ip": ip,
            "ports": sorted(set(ports)),
            "services": [
                {
                    "port": s.get('port'),
                    "service_name": s.get('protocol'),
                    "transport_protocol": s.get('transport_protocol')
                }
                for s in services[:10]
            ],
            "services_count": len(services),
            "autonomous_system": {
                "asn": asn_info.get('asn'),
                "name": asn_info.get('name'),
                "country_code": asn_info.get('country_code')
            },
            "location": {
                "country": location.get('country'),
                "country_code": location.get('country_code'),
                "city": location.get('city'),
                "coordinates": location.get('coordinates')
            },
            "dns_names": dns_names[:20] if dns_names else [],
            "last_updated": host_data.get('last_updated_at')
        }

        return {
            "success": True,
            "data": summary
        }

    def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal para obtener datos de Censys

        Args:
            params: Diccionario con parámetros:
                - query_type: 'get_host_summary' o 'view_host'
                - ip: IP para consultar

        Returns:
            Diccionario con los resultados
        """
        query_type = params.get('query_type', 'get_host_summary')

        results = {
            "provider": self.get_name(),
            "version": self.get_version(),
            "query_type": query_type,
            "timestamp": datetime.now().isoformat()
        }

        if not self.api_token:
            results['error'] = "CENSYS_API_TOKEN no configurada"
            return results

        ip = params.get('ip')
        if not ip:
            results['error'] = "Parámetro 'ip' requerido"
            return results

        if query_type == 'get_host_summary':
            summary_result = self.get_host_summary(ip)
            if summary_result.get('success'):
                results['data'] = summary_result['data']
            else:
                results['error'] = summary_result.get('error')

        elif query_type == 'view_host':
            view_result = self.view_host(ip)
            if view_result.get('success'):
                results['data'] = view_result['data']
            else:
                results['error'] = view_result.get('error')

        else:
            results['error'] = f"query_type '{query_type}' no soportado"
            results['supported_types'] = ['get_host_summary', 'view_host']

        return results
