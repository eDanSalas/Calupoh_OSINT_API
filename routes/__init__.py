#!/usr/bin/env python3
"""Paquete de rutas"""
from .main import main_bp
from .auth import auth_bp
from .providers import providers_bp
from .search import search_bp

__all__ = ['main_bp', 'auth_bp', 'providers_bp', 'search_bp']
