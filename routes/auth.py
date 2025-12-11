#!/usr/bin/env python3
"""
Rutas de autenticación (local y Google OAuth)
"""
import json
import base64
import logging
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from config import Config

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Registra un nuevo usuario local"""
    from flask import current_app
    
    user_manager = current_app.config['USER_MANAGER']
    data = request.json
    
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password:
        return jsonify({"error": "Usuario y contraseña requeridos"}), 400

    result = user_manager.register_user(username, password, email)

    if result['success']:
        logging.info(f"👤 Nuevo usuario registrado: {username}")
        return jsonify(result), 201
    else:
        return jsonify(result), 409


@auth_bp.route('/login', methods=['POST'])
def login():
    """Inicia sesión local y devuelve JWT"""
    from flask import current_app
    
    user_manager = current_app.config['USER_MANAGER']
    data = request.json
    
    username = data.get('username')
    password = data.get('password')

    if user_manager.login_user(username, password):
        access_token = create_access_token(identity=username)
        logging.info(f"🔑 Login exitoso: {username}")
        return jsonify({
            "msg": "Login exitoso",
            "access_token": access_token,
            "user": username
        }), 200
    else:
        logging.warning(f"⛔ Intento de login fallido: {username}")
        return jsonify({"error": "Credenciales inválidas"}), 401


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """Ruta protegida - requiere JWT"""
    current_user = get_jwt_identity()
    return jsonify({"logged_in_as": current_user, "access": "granted"}), 200


@auth_bp.route('/google/login')
def google_login():
    """Inicia el flujo de OAuth con Google"""
    from flask import current_app
    
    google = current_app.config['GOOGLE_OAUTH']
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """Callback de Google OAuth"""
    from flask import current_app
    
    try:
        google = current_app.config['GOOGLE_OAUTH']
        user_manager = current_app.config['USER_MANAGER']
        
        token = google.authorize_access_token()
        resp = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
        user_info = resp.json()

        result = user_manager.register_or_update_google_user(user_info)

        if result['success']:
            username = result['username']
            access_token = create_access_token(identity=username)

            user_data_json = json.dumps(user_info)
            user_data_b64 = base64.b64encode(user_data_json.encode('utf-8')).decode('utf-8')

            return redirect(f"{Config.FRONTEND_URL}/?token={access_token}&user={user_data_b64}")

    except Exception as e:
        logging.error(f"Error en Google Auth: {e}")
        return jsonify({"error": "Fallo en autenticación con Google", "details": str(e)}), 500
