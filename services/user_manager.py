#!/usr/bin/env python3
"""
Gestor de usuarios con autenticación local y OAuth
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from flask_bcrypt import Bcrypt
from typing import Dict, Any

from config import Config
from services.crypto import CryptoManager
from services.replication import ReplicationManager


class UserManager:
    """Gestor de usuarios con persistencia local, HDFS y encriptada"""

    def __init__(self, crypto_manager: CryptoManager, bcrypt: Bcrypt):
        """
        Inicializa el gestor de usuarios

        Args:
            crypto_manager: Instancia del gestor de encriptación
            bcrypt: Instancia de Flask-Bcrypt
        """
        self.crypto = crypto_manager
        self.bcrypt = bcrypt
        self.db_file = Config.OUTPUT_DIR / "users_db.json"
        self._init_db()

    def _init_db(self):
        """Inicializa la base de datos de usuarios si no existe"""
        if not self.db_file.exists():
            with open(self.db_file, 'w') as f:
                json.dump({"users": {}}, f)

    def _save_db(self, data: Dict):
        """Guarda la base de datos de usuarios"""
        with open(self.db_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_db(self) -> Dict:
        """Carga la base de datos de usuarios"""
        with open(self.db_file, 'r') as f:
            return json.load(f)

    def _process_storage(self, username: str, user_data: Dict[str, Any]):
        """
        Procesa el almacenamiento de datos del usuario
        Guarda archivos planos y encriptados, y replica a HDFS y servidor secundario

        Args:
            username: Nombre de usuario
            user_data: Datos del usuario a almacenar
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"user_{username}_{timestamp}"

        # A) Archivo Plano
        plain_file = Config.OUTPUT_DIR / f"{filename_base}_plain.json"
        with open(plain_file, 'w') as f:
            json.dump(user_data, f, indent=2)

        # B) Archivo Encriptado
        encrypted_chunks = self.crypto.encrypt_data(user_data)
        enc_file = Config.OUTPUT_DIR / f"{filename_base}_encrypted.json"
        with open(enc_file, 'w') as f:
            json.dump({
                "username": username,
                "data": encrypted_chunks,
                "timestamp": timestamp,
                "provider": user_data.get('provider', 'local')
            }, f)

        # C) Replicación (HDFS Local + SCP Remoto)
        ReplicationManager.store_and_replicate(self.db_file)
        ReplicationManager.store_and_replicate(plain_file)
        ReplicationManager.store_and_replicate(enc_file)

    def register_user(self, username: str, password: str, email: str = None) -> Dict[str, Any]:
        """
        Registra un nuevo usuario con autenticación local

        Args:
            username: Nombre de usuario
            password: Contraseña
            email: Email opcional

        Returns:
            Diccionario con el resultado de la operación
        """
        db = self._load_db()
        
        if username in db['users']:
            return {"success": False, "error": "El usuario ya existe"}

        pw_hash = self.bcrypt.generate_password_hash(password).decode('utf-8')
        user_data = {
            "username": username,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "role": "user",
            "provider": "local",
            "active": True
        }

        db['users'][username] = {"hash": pw_hash, "profile": user_data}
        self._save_db(db)

        self._process_storage(username, user_data)
        return {"success": True, "msg": "Usuario registrado y replicado"}

    def login_user(self, username: str, password: str) -> bool:
        """
        Verifica las credenciales de un usuario local

        Args:
            username: Nombre de usuario
            password: Contraseña

        Returns:
            True si las credenciales son válidas, False en caso contrario
        """
        db = self._load_db()
        
        if username not in db['users']:
            return False

        user_record = db['users'][username]

        # Verificar que sea usuario local (Google users no tienen password hash)
        if user_record['profile'].get('provider') == 'google':
            return False

        stored_hash = user_record.get('hash')
        if stored_hash is None:
            return False

        return self.bcrypt.check_password_hash(stored_hash, password)

    def register_or_update_google_user(self, google_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra o actualiza un usuario de Google OAuth

        Args:
            google_info: Información del usuario desde Google

        Returns:
            Diccionario con el resultado de la operación
        """
        db = self._load_db()
        email = google_info.get('email')
        name = google_info.get('name')

        # Usamos el email como identificador único
        username = email
        is_new = False

        if username not in db['users']:
            is_new = True
            logging.info(f"🆕 Registrando nuevo usuario Google: {email}")

            user_data = {
                "username": username,
                "email": email,
                "full_name": name,
                "picture": google_info.get('picture'),
                "created_at": datetime.now().isoformat(),
                "role": "user",
                "provider": "google",
                "active": True
            }

            # Guardar en DB (Hash es None porque usa OAuth)
            db['users'][username] = {"hash": None, "profile": user_data}
            self._save_db(db)

            # Disparar proceso de almacenamiento
            self._process_storage(username, user_data)
        else:
            logging.info(f"👋 Usuario Google existente: {email}")

        return {"success": True, "username": username, "is_new": is_new}
