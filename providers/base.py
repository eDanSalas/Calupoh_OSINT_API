#!/usr/bin/env python3
"""
Clase base abstracta para todos los providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseProvider(ABC):
    """Clase base abstracta para todos los providers de datos"""

    @abstractmethod
    def get_name(self) -> str:
        """Retorna el nombre del provider"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Retorna la versión del provider"""
        pass

    @abstractmethod
    def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene datos del servicio externo

        Args:
            params: Parámetros para la consulta

        Returns:
            Diccionario con los datos obtenidos
        """
        pass

    @abstractmethod
    def get_available_endpoints(self) -> List[Dict[str, str]]:
        """Retorna lista de endpoints disponibles en el provider"""
        pass
