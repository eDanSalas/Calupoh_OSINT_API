#!/usr/bin/env python3
"""
Otros providers: SerpStack, IPAPI, PeeringDB
"""
import os
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List
from urllib.parse import urlparse
from .base import BaseProvider


class SerpStackProvider(BaseProvider):
    """Provider para SerpStack - Google SERP Scraping API"""

    BASE_URL = "https://api.serpstack.com"

    def __init__(self):
        self.api_key = os.getenv('SERPSTACK_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SecureDataProvider/2.3.0'
        })

    def get_name(self) -> str:
        return "serpstack"

    def get_version(self) -> str:
        return "1.0.0"

    def get_available_endpoints(self) -> List[Dict[str, str]]:
        return [
            {"type": "search", "description": "Buscar en Google", "requires_api_key": True},
            {"type": "extract_urls", "description": "Extraer URLs", "requires_api_key": True},
            {"type": "extract_domains", "description": "Extraer dominios", "requires_api_key": True}
        ]

    def search(self, query: str, num: int = 10, location: str = None) -> Dict[str, Any]:
        """Busca en Google"""
        if not self.api_key:
            return {"success": False, "error": "SERPSTACK_API_KEY no configurada"}

        params = {'access_key': self.api_key, 'query': query, 'num': min(num, 100)}
        if location:
            params['location'] = location

        try:
            response = self.session.get(f"{self.BASE_URL}/search", params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                return {"success": False, "error": data['error'].get('info')}

            return {"success": True, "data": data}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def extract_domains(self, query: str, num: int = 10) -> Dict[str, Any]:
        """Extrae dominios únicos"""
        result = self.search(query, num)
        if not result.get('success'):
            return result

        domains = {}
        for item in result['data'].get('organic_results', []):
            try:
                parsed = urlparse(item.get('url', ''))
                domain = (parsed.netloc or parsed.path.split('/')[0]).replace('www.', '')
                
                if domain and domain not in domains:
                    domains[domain] = {
                        'domain': domain,
                        'url': item['url'],
                        'title': item.get('title'),
                        'first_seen_position': item.get('position')
                    }
            except:
                continue

        return {"success": True, "query": query, "total_domains": len(domains), "domains": list(domains.values())}

    def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query_type = params.get('query_type', 'search')
        results = {
            "provider": self.get_name(),
            "version": self.get_version(),
            "query_type": query_type,
            "timestamp": datetime.now().isoformat()
        }

        query = params.get('query')
        if not query:
            results['error'] = "Parámetro 'query' requerido"
            return results

        if query_type == 'search':
            results['data'] = self.search(query, params.get('num', 10), params.get('location'))
        elif query_type == 'extract_domains':
            results['data'] = self.extract_domains(query, params.get('num', 10))
        else:
            results['error'] = f"query_type '{query_type}' no soportado"

        return results


class IPAPIProvider(BaseProvider):
    """Provider para IP-API.com"""

    BASE_URL = "http://ip-api.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'SecureDataProvider/2.0'})

    def get_name(self) -> str:
        return "ipapi"

    def get_version(self) -> str:
        return "1.0.0"

    def get_available_endpoints(self) -> List[Dict[str, str]]:
        return [
            {"type": "lookup", "description": "Geolocalización de IP", "requires_api_key": False},
            {"type": "batch", "description": "Múltiples IPs", "requires_api_key": False}
        ]

    def lookup(self, ip: str = None, fields: List[str] = None, lang: str = 'en') -> Dict[str, Any]:
        """Obtiene geolocalización"""
        endpoint = f"/json/{ip}" if ip else "/json/"
        params = {}
        if fields:
            params['fields'] = ','.join(fields)
        if lang != 'en':
            params['lang'] = lang

        try:
            response = self.session.get(f"{self.BASE_URL}{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if isinstance(result, dict) and result.get('status') == 'fail':
                return {"success": False, "error": result.get('message')}

            return {"success": True, "data": result}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query_type = params.get('query_type', 'lookup')
        results = {
            "provider": self.get_name(),
            "version": self.get_version(),
            "query_type": query_type,
            "timestamp": datetime.now().isoformat()
        }

        if query_type == 'lookup':
            results['data'] = self.lookup(params.get('ip'), params.get('fields'), params.get('lang', 'en'))
        else:
            results['error'] = f"query_type '{query_type}' no soportado"

        return results


class PeeringDBProvider(BaseProvider):
    """Provider para PeeringDB"""

    BASE_URL = "https://www.peeringdb.com/api"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'SecureDataProvider/2.4.0', 'Accept': 'application/json'})

    def get_name(self) -> str:
        return "peeringdb"

    def get_version(self) -> str:
        return "1.0.0"

    def get_available_endpoints(self) -> List[Dict[str, str]]:
        return [
            {"type": "get_network_by_asn", "description": "Info de red por ASN", "requires_api_key": False},
            {"type": "get_asn_summary", "description": "Resumen completo ASN", "requires_api_key": False}
        ]

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        try:
            response = self.session.get(f"{self.BASE_URL}{endpoint}", params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            return {"success": True, "data": data.get('data', []), "meta": data.get('meta', {})}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_network_by_asn(self, asn: int) -> Dict[str, Any]:
        result = self._make_request('/net', {'asn': asn, 'depth': 2})
        if result.get('success') and result.get('data'):
            return {"success": True, "data": result['data'][0] if result['data'] else None}
        return result

    def get_asn_summary(self, asn: int) -> Dict[str, Any]:
        net_result = self.get_network_by_asn(asn)
        if not net_result.get('success'):
            return net_result

        summary = {"asn": asn, "network": net_result.get('data')}
        return {"success": True, "data": summary}

    def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query_type = params.get('query_type', 'get_network_by_asn')
        results = {
            "provider": self.get_name(),
            "version": self.get_version(),
            "query_type": query_type,
            "timestamp": datetime.now().isoformat()
        }

        asn = params.get('asn')
        if not asn:
            results['error'] = "Parámetro 'asn' requerido"
            return results

        if query_type == 'get_network_by_asn':
            results['data'] = self.get_network_by_asn(asn)
        elif query_type == 'get_asn_summary':
            results['data'] = self.get_asn_summary(asn)
        else:
            results['error'] = f"query_type '{query_type}' no soportado"

        return results
