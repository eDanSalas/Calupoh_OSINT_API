#!/usr/bin/env python3
"""
Provider para servicios de Cloudflare (Trace y Geolocation)
"""
import requests
from datetime import datetime
from typing import Dict, Any, List
from .base import BaseProvider


class CloudflareProvider(BaseProvider):
    """Provider para servicios de Cloudflare (Trace y Geolocation)"""

    # Endpoints disponibles de Cloudflare
    TRACE_ENDPOINTS = [
        "https://one.one.one.one/cdn-cgi/trace",
        "https://1.0.0.1/cdn-cgi/trace",
        "https://cloudflare-dns.com/cdn-cgi/trace",
        "https://cloudflare-eth.com/cdn-cgi/trace",
        "https://workers.dev/cdn-cgi/trace",
        "https://pages.dev/cdn-cgi/trace",
        "https://cloudflare.tv/cdn-cgi/trace",
        "https://icanhazip.com/cdn-cgi/trace"
    ]

    GEOLOCATION_ENDPOINT = "https://speed.cloudflare.com/meta"
    GEOLOCATION_HEADERS_ENDPOINT = "https://speed.cloudflare.com/__down"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; CloudflareTraceFetcher/1.0)'
        })

    def get_name(self) -> str:
        return "cloudflare"

    def get_version(self) -> str:
        return "1.0.0"

    def get_available_endpoints(self) -> List[Dict[str, str]]:
        """Retorna información sobre los endpoints disponibles"""
        return [
            {
                "type": "trace",
                "description": "Cloudflare Trace API - Información de IP, ubicación, TLS, etc.",
                "endpoints": self.TRACE_ENDPOINTS
            },
            {
                "type": "geolocation",
                "description": "Cloudflare Geolocation API - Información detallada de geolocalización",
                "endpoint": self.GEOLOCATION_ENDPOINT
            },
            {
                "type": "geolocation_headers",
                "description": "Cloudflare Geolocation en Headers - Metadatos en cabeceras HTTP",
                "endpoint": self.GEOLOCATION_HEADERS_ENDPOINT
            }
        ]

    def _parse_trace_response(self, text: str) -> Dict[str, str]:
        """
        Parsea la respuesta del formato trace (key=value) a diccionario

        Args:
            text: Texto en formato key=value (uno por línea)

        Returns:
            Diccionario con los pares clave-valor
        """
        result = {}
        for line in text.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                result[key.strip()] = value.strip()
        return result

    def fetch_trace(self, endpoint: str = None, timeout: int = 10) -> Dict[str, Any]:
        """
        Obtiene información del Cloudflare Trace API

        Args:
            endpoint: URL específica del trace (usa la primera por defecto)
            timeout: Timeout de la petición en segundos

        Returns:
            Diccionario con la información parseada
        """
        url = endpoint or self.TRACE_ENDPOINTS[0]

        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()

            parsed_data = self._parse_trace_response(response.text)

            return {
                "success": True,
                "endpoint": url,
                "data": parsed_data,
                "raw_response": response.text
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "endpoint": url,
                "error": str(e)
            }

    def fetch_geolocation(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Obtiene información del Cloudflare Geolocation API (JSON)

        Args:
            timeout: Timeout de la petición en segundos

        Returns:
            Diccionario con la información de geolocalización
        """
        try:
            response = self.session.get(self.GEOLOCATION_ENDPOINT, timeout=timeout)
            response.raise_for_status()

            return {
                "success": True,
                "endpoint": self.GEOLOCATION_ENDPOINT,
                "data": response.json()
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "endpoint": self.GEOLOCATION_ENDPOINT,
                "error": str(e)
            }

    def fetch_geolocation_headers(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Obtiene información del Cloudflare Geolocation desde headers

        Args:
            timeout: Timeout de la petición en segundos

        Returns:
            Diccionario con los headers cf-meta-*
        """
        try:
            response = self.session.get(self.GEOLOCATION_HEADERS_ENDPOINT, timeout=timeout)
            response.raise_for_status()

            # Extraer solo los headers que empiezan con cf-meta-
            cf_headers = {
                key: value
                for key, value in response.headers.items()
                if key.lower().startswith('cf-meta-')
            }

            return {
                "success": True,
                "endpoint": self.GEOLOCATION_HEADERS_ENDPOINT,
                "data": cf_headers
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "endpoint": self.GEOLOCATION_HEADERS_ENDPOINT,
                "error": str(e)
            }

    def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal para obtener datos de Cloudflare

        Args:
            params: Diccionario con parámetros:
                - query_type: 'trace', 'geolocation', 'geolocation_headers', o 'all'
                - endpoint: (opcional) URL específica para trace
                - timeout: (opcional) Timeout en segundos

        Returns:
            Diccionario con los resultados
        """
        query_type = params.get('query_type', 'trace')
        timeout = params.get('timeout', 10)

        results = {
            "provider": self.get_name(),
            "version": self.get_version(),
            "query_type": query_type,
            "timestamp": datetime.now().isoformat()
        }

        if query_type == 'trace':
            endpoint = params.get('endpoint')
            results['trace'] = self.fetch_trace(endpoint, timeout)

        elif query_type == 'geolocation':
            results['geolocation'] = self.fetch_geolocation(timeout)

        elif query_type == 'geolocation_headers':
            results['geolocation_headers'] = self.fetch_geolocation_headers(timeout)

        elif query_type == 'all':
            results['trace'] = self.fetch_trace(timeout=timeout)
            results['geolocation'] = self.fetch_geolocation(timeout)
            results['geolocation_headers'] = self.fetch_geolocation_headers(timeout)

        else:
            results['error'] = f"Tipo de consulta no válido: {query_type}"
            results['valid_types'] = ['trace', 'geolocation', 'geolocation_headers', 'all']

        return results
