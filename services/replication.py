#!/usr/bin/env python3
"""
Servicio de replicación a HDFS y servidor secundario
"""
import logging
import subprocess
from pathlib import Path
from config import Config


class ReplicationManager:
    """Gestiona el almacenamiento en HDFS local y la replicación al nodo secundario"""

    @staticmethod
    def store_and_replicate(file_path: Path) -> bool:
        """
        1. Guarda en HDFS local (Servidor 1)
        2. Copia vía SCP al Servidor 2

        Args:
            file_path: Ruta del archivo a replicar

        Returns:
            True si la replicación fue exitosa, False en caso contrario
        """
        if not file_path.exists():
            logging.error(f"❌ Archivo no existe: {file_path}")
            return False

        filename = file_path.name

        # PASO 1: Guardar en HDFS local
        try:
            logging.info(f"💾 Guardando {filename} en HDFS (Servidor 1)...")
            hdfs_cmd = [
                "sudo", "-u", Config.REPLICATION_USER,
                Config.HADOOP_BIN, "dfs", "-put", "-f",
                str(file_path), "/"
            ]
            subprocess.run(hdfs_cmd, capture_output=True, text=True, check=False)
        except Exception as e:
            logging.error(f"❌ Error ejecutando HDFS: {e}")

        # PASO 2: Replicar a Servidor 2 (SCP)
        remote_path = f"{Config.REPLICATION_USER}@{Config.SECONDARY_SERVER_IP}:{Config.REMOTE_DEST_DIR}/{filename}"
        logging.info(f"🔄 Replicando {filename} a {Config.SECONDARY_SERVER_IP}...")

        try:
            cmd_scp = [
                "scp",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                str(file_path),
                remote_path
            ]
            result_scp = subprocess.run(cmd_scp, capture_output=True, text=True)

            if result_scp.returncode == 0:
                logging.info(f"✅ Replicación SCP exitosa: {filename}")
                return True
            else:
                logging.error(f"❌ Falló replicación SCP: {result_scp.stderr}")
                return False

        except Exception as e:
            logging.error(f"❌ Error crítico en SCP: {e}")
            return False
