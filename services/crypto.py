#!/usr/bin/env python3
"""
Servicio de encriptación RSA para proteger datos sensibles
"""
import json
import base64
import hashlib
from typing import Dict, Any, List
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


class CryptoManager:
    """Gestor de encriptación RSA para proteger datos sensibles"""

    def __init__(self, keys_dir: Path):
        """
        Inicializa el gestor de encriptación
        
        Args:
            keys_dir: Directorio donde se guardarán las llaves
        """
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        self.private_key = None
        self.public_key = None
        self._generate_keys()

    def _generate_keys(self):
        """Genera un par de llaves RSA pública/privada"""
        print("🔐 Generando llaves RSA (esto puede tardar)...", flush=True)
        
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

        # Serializar llaves
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Guardar en archivos
        with open(self.keys_dir / "private_key.pem", "wb") as f:
            f.write(private_pem)

        with open(self.keys_dir / "public_key.pem", "wb") as f:
            f.write(public_pem)
        
        print(f"✅ Llaves generadas y guardadas en {self.keys_dir}", flush=True)

    def encrypt_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Encripta datos usando RSA-OAEP

        Args:
            data: Diccionario de datos a encriptar

        Returns:
            Lista de chunks encriptados en base64
        """
        json_data = json.dumps(data)

        # RSA 2048 puede encriptar máximo 190 bytes con OAEP SHA-256
        max_chunk_size = 190
        chunks = [json_data[i:i+max_chunk_size] for i in range(0, len(json_data), max_chunk_size)]

        encrypted_chunks = []
        for chunk in chunks:
            encrypted = self.public_key.encrypt(
                chunk.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            encrypted_chunks.append(base64.b64encode(encrypted).decode())

        return encrypted_chunks

    def create_sha256_hash(self, data: Dict[str, Any]) -> str:
        """
        Crea un hash SHA-256 de los datos

        Args:
            data: Diccionario de datos a hashear

        Returns:
            Hash SHA-256 en hexadecimal
        """
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
