#!/usr/bin/env python3
"""
Registro centralizado de providers disponibles
"""
import logging
from typing import Dict, Any, List
from providers.base import BaseProvider


class ProviderRegistry:
    """Registro centralizado de providers disponibles"""

    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider):
        """
        Registra un nuevo provider

        Args:
            provider: Instancia del provider a registrar
        """
        self.providers[provider.get_name()] = provider
        logging.info(f"✅ Provider registrado: {provider.get_name()} v{provider.get_version()}")

    def get_provider(self, name: str) -> BaseProvider:
        """
        Obtiene un provider por nombre

        Args:
            name: Nombre del provider

        Returns:
            Instancia del provider o None si no existe
        """
        return self.providers.get(name)

    def list_providers(self) -> List[Dict[str, Any]]:
        """
        Lista todos los providers disponibles

        Returns:
            Lista de diccionarios con información de cada provider
        """
        return [
            {
                "name": provider.get_name(),
                "version": provider.get_version(),
                "endpoints": provider.get_available_endpoints()
            }
            for provider in self.providers.values()
        ]
