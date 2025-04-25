#!/usr/bin/env python3

import datetime
import logging
import asyncio
import os
import json
import random
import hashlib
import uuid
from time import time

import aiocoap.resource as resource
import aiocoap
from aiocoap.numbers.contentformat import ContentFormat

# Configuration - Sécurité améliorée
RESOURCE_PATH = "data_capteurs"
DEBUG_MODE = True  # Mode debug activé
ALLOW_ALL_ORIGINS = False  # CORS restreint
SECRET_KEY = "iot_master_key_123"  # Clé secrète pour générer des tokens

# Paramètres d'authentification
AUTH_REQUIRED = True  # Authentification obligatoire
TOKEN_EXPIRY_TIME = 3600  # Durée de validité des tokens en secondes (1 heure)

# Utilisateurs autorisés (username: password_hash)

AUTHORIZED_USERS = {
    "admin": hashlib.sha256("admin_password".encode()).hexdigest(),
    "sensor1": hashlib.sha256("sensor1_secret".encode()).hexdigest(),
    "sensor2": hashlib.sha256("sensor2_secret".encode()).hexdigest()
}

# Stockage des tokens valides: {token: {"username": username, "expires": timestamp}}
VALID_TOKENS = {}

# Simulation de base de données de capteurs (en mémoire)
sensors_db = {
    "temperature": [],
    "sound": [],
    "presence": [],
    "all": []  # Pour stocker toutes les données ensemble
}

def generate_token(username):
    """Génère un token d'authentification pour un utilisateur."""
    token = str(uuid.uuid4())
    expires = time() + TOKEN_EXPIRY_TIME
    VALID_TOKENS[token] = {"username": username, "expires": expires}
    return token, expires

def validate_token(request):
    """Valide un token d'authentification."""
    token = None
    
    # Extraire le token de l'en-tête d'options CoAP
    for option in request.opt.option_list():
        if option.number == aiocoap.numbers.optionnumbers.OptionNumber.URI_QUERY:
            # Gérer correctement que la valeur soit bytes ou str
            if isinstance(option.value, bytes):
                param = option.value.decode('utf-8')
            else:
                param = option.value  # Utiliser directement si c'est déjà une chaîne
                
            if param.startswith("token="):
                token = param[6:]  # Extraire la valeur après "token="
    
    if not token or token not in VALID_TOKENS:
        return False, "Token invalide ou manquant"
    
    token_data = VALID_TOKENS[token]
    
    # Vérifier si le token a expiré
    if token_data["expires"] < time():
        del VALID_TOKENS[token]  # Supprimer le token expiré
        return False, "Token expiré"
    
    return True, token_data["username"]

class AuthResource(resource.Resource):
    """Ressource pour l'authentification et la génération de tokens."""
    
    async def render_post(self, request):
        try:
            credentials = json.loads(request.payload.decode('utf-8'))
            
            # Vérification des champs requis
            if "username" not in credentials or "password" not in credentials:
                return aiocoap.Message(code=aiocoap.UNAUTHORIZED, 
                                      payload=json.dumps({"error": "Nom d'utilisateur et mot de passe requis"}).encode('utf-8'))
            
            username = credentials["username"]
            password = credentials["password"]
            
            # Vérification des credentials
            if username not in AUTHORIZED_USERS:
                return aiocoap.Message(code=aiocoap.UNAUTHORIZED, 
                                      payload=json.dumps({"error": "Utilisateur inconnu"}).encode('utf-8'))
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if AUTHORIZED_USERS[username] != password_hash:
                return aiocoap.Message(code=aiocoap.UNAUTHORIZED, 
                                      payload=json.dumps({"error": "Mot de passe incorrect"}).encode('utf-8'))
            
            # Génération du token
            token, expires = generate_token(username)
            
            if DEBUG_MODE:
                print(f"[DEBUG] Token généré pour l'utilisateur {username}")
            
            response = {
                "token": token,
                "expires": expires,
                "expires_in": TOKEN_EXPIRY_TIME
            }
            
            return aiocoap.Message(code=aiocoap.CREATED, 
                                  payload=json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=b"Format JSON invalide")
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] Erreur d'authentification: {str(e)}")
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR, 
                                  payload=json.dumps({"error": str(e)}).encode('utf-8'))

class SensorResource(resource.Resource):
    """Resource CoAP pour un type de capteur spécifique."""
    
    def __init__(self, sensor_type):
        super().__init__()
        self.sensor_type = sensor_type
        self.content = f"Capteur {sensor_type} pret a recevoir des donnees".encode('utf-8')
        
    async def render_get(self, request):
        # Vérification de l'authentification
        if AUTH_REQUIRED:
            is_valid, message = validate_token(request)
            if not is_valid:
                return aiocoap.Message(code=aiocoap.UNAUTHORIZED, payload=json.dumps({"error": message}).encode('utf-8'))
            
            username = message  # message contient le nom d'utilisateur si le token est valide
        
        if self.sensor_type in sensors_db and sensors_db[self.sensor_type]:
            response_data = {
                "sensor_type": self.sensor_type,
                "readings": sensors_db[self.sensor_type],
                "count": len(sensors_db[self.sensor_type]),
                "last_updated": datetime.datetime.now().isoformat()
            }
        else:
            response_data = {
                "sensor_type": self.sensor_type,
                "readings": [],
                "count": 0,
                "status": "Aucune donnee disponible"
            }
            
        response_json = json.dumps(response_data)
        
        # Log avec informations utilisateur
        if DEBUG_MODE:
            if AUTH_REQUIRED:
                print(f"[DEBUG] Requete GET pour capteur {self.sensor_type} de {request.remote} (utilisateur: {username})")
            else:
                print(f"[DEBUG] Requete GET pour capteur {self.sensor_type} de {request.remote}")
        
        return aiocoap.Message(payload=response_json.encode('utf-8'))

    async def render_put(self, request):
        # Vérification de l'authentification
        if AUTH_REQUIRED:
            is_valid, message = validate_token(request)
            if not is_valid:
                return aiocoap.Message(code=aiocoap.UNAUTHORIZED, payload=json.dumps({"error": message}).encode('utf-8'))
            
            username = message  # message contient le nom d'utilisateur si le token est valide
        
        try:
            sensor_data = json.loads(request.payload.decode('utf-8'))
            
            # Validation minimale des données
            if not isinstance(sensor_data, dict):
                return aiocoap.Message(code=aiocoap.BAD_REQUEST, 
                                      payload=json.dumps({"error": "Format de données invalide"}).encode('utf-8'))
            
            # Ajoute un timestamp si non présent
            if "timestamp" not in sensor_data:
                sensor_data["timestamp"] = time()
                
            # Ajoute l'ID du capteur et l'utilisateur dans les données
            sensor_data["sensor_type"] = self.sensor_type
            if AUTH_REQUIRED:
                sensor_data["recorded_by"] = username
            
            # Stocke les données
            sensors_db[self.sensor_type].append(sensor_data)
            sensors_db["all"].append(sensor_data)
            
            # Écriture sécurisée dans le système de fichiers
            try:
                os.makedirs(RESOURCE_PATH, exist_ok=True)
                filename = f"{RESOURCE_PATH}/{self.sensor_type}_{datetime.datetime.now().timestamp()}.json"
                with open(filename, "w") as f:
                    json.dump(sensor_data, f)
            except Exception as e:
                print(f"Erreur d'écriture: {e}")
            
            # Log avec informations utilisateur
            if DEBUG_MODE:
                if AUTH_REQUIRED:
                    print(f"[DEBUG] Données {self.sensor_type} reçues de {request.remote} (utilisateur: {username})")
                else:
                    print(f"[DEBUG] Données {self.sensor_type} reçues de {request.remote}")
                print(f"[DEBUG] Contenu: {sensor_data}")
            
            response = {
                "status": "success",
                "message": f"Données {self.sensor_type} enregistrées avec succès",
                "data_count": len(sensors_db[self.sensor_type])
            }
            
            return aiocoap.Message(code=aiocoap.CHANGED, payload=json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=json.dumps({"error": "Format JSON invalide"}).encode('utf-8'))
        except Exception as e:
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR, 
                                  payload=json.dumps({"error": str(e)}).encode('utf-8'))


class AllSensorsResource(resource.Resource):
    """Resource pour accéder à toutes les données des capteurs."""
    
    async def render_get(self, request):
        # Vérification de l'authentification
        if AUTH_REQUIRED:
            is_valid, message = validate_token(request)
            if not is_valid:
                return aiocoap.Message(code=aiocoap.UNAUTHORIZED, payload=json.dumps({"error": message}).encode('utf-8'))
            
            username = message  # message contient le nom d'utilisateur si le token est valide
        
        response_data = {
            "sensors": {
                "temperature": {
                    "count": len(sensors_db["temperature"]),
                    "data": sensors_db["temperature"]
                },
                "sound": {
                    "count": len(sensors_db["sound"]),
                    "data": sensors_db["sound"]
                },
                "presence": {
                    "count": len(sensors_db["presence"]),
                    "data": sensors_db["presence"]
                }
            },
            "total_readings": len(sensors_db["all"]),
            "system_time": datetime.datetime.now().isoformat()
        }
        
        # Log avec informations utilisateur
        if DEBUG_MODE:
            if AUTH_REQUIRED:
                print(f"[DEBUG] Requête GET pour tous les capteurs de {request.remote} (utilisateur: {username})")
            else:
                print(f"[DEBUG] Requête GET pour tous les capteurs de {request.remote}")
        
        return aiocoap.Message(payload=json.dumps(response_data).encode('utf-8'))


class ConfigResource(resource.Resource):
    """Resource pour la configuration du système de capteurs."""
    
    def __init__(self):
        super().__init__()
        self.config = {
            "sampling_rate": 5,  # secondes
            "alert_threshold": {
                "temperature": {"min": 15, "max": 30},
                "sound": {"min": 0, "max": 100},
                "presence": {"sensitivity": "high"}
            },
            "debug_mode": DEBUG_MODE
        }
        
        # Configuration sensible séparée (non accessible directement)
        self.sensitive_config = {
            "admin_password": hashlib.sha256("admin_password".encode()).hexdigest(),
            "master_key": SECRET_KEY,
            "backup_server": "192.168.1.100"
        }
        
    async def render_get(self, request):
        # Vérification de l'authentification
        if AUTH_REQUIRED:
            is_valid, message = validate_token(request)
            if not is_valid:
                return aiocoap.Message(code=aiocoap.UNAUTHORIZED, payload=json.dumps({"error": message}).encode('utf-8'))
            
            username = message  # message contient le nom d'utilisateur si le token est valide

        # On ne retourne que la configuration non sensible
        return aiocoap.Message(payload=json.dumps(self.config).encode('utf-8'))
        
    async def render_put(self, request):
        # Vérification de l'authentification
        if AUTH_REQUIRED:
            is_valid, message = validate_token(request)
            if not is_valid:
                return aiocoap.Message(code=aiocoap.UNAUTHORIZED, payload=json.dumps({"error": message}).encode('utf-8'))
            
            username = message  # message contient le nom d'utilisateur si le token est valide
            
            # Vérification que l'utilisateur est admin
            if username != "admin":
                return aiocoap.Message(code=aiocoap.FORBIDDEN, 
                                      payload=json.dumps({"error": "Droits d'administrateur requis"}).encode('utf-8'))
        
        try:
            new_config = json.loads(request.payload.decode('utf-8'))
            
            # Validation des données de configuration
            if not isinstance(new_config, dict):
                return aiocoap.Message(code=aiocoap.BAD_REQUEST, 
                                      payload=json.dumps({"error": "Format de configuration invalide"}).encode('utf-8'))
            
            # Limiter les champs modifiables (sécurité)
            allowed_keys = ["sampling_rate", "alert_threshold", "debug_mode"]
            filtered_config = {k: v for k, v in new_config.items() if k in allowed_keys}
            
            # Mise à jour de la configuration
            self.config.update(filtered_config)
            
            # Log avec informations utilisateur
            if DEBUG_MODE:
                if AUTH_REQUIRED:
                    print(f"[DEBUG] Configuration mise à jour par {request.remote} (utilisateur: {username})")
                else:
                    print(f"[DEBUG] Configuration mise à jour par {request.remote}")
                print(f"[DEBUG] Nouvelle config: {self.config}")
            
            return aiocoap.Message(code=aiocoap.CHANGED, 
                                  payload=json.dumps({"status": "Configuration mise à jour"}).encode('utf-8'))
        except json.JSONDecodeError:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, 
                                  payload=json.dumps({"error": "Format JSON invalide"}).encode('utf-8'))
        except Exception as e:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, 
                                  payload=json.dumps({"error": str(e)}).encode('utf-8'))


class StatusResource(resource.Resource):
    """Ressource pour afficher le statut du serveur."""
    
    async def render_get(self, request):
        # Vérification de l'authentification
        if AUTH_REQUIRED:
            is_valid, message = validate_token(request)
            if not is_valid:
                return aiocoap.Message(code=aiocoap.UNAUTHORIZED, payload=json.dumps({"error": message}).encode('utf-8'))
            
            username = message  # message contient le nom d'utilisateur si le token est valide
        
        # Information de statut sans risque d'exécution de commandes
        status_data = {
            "server_status": "running",
            "version": "1.0.0",
            "uptime": "since " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sensors_count": {
                "temperature": len(sensors_db["temperature"]),
                "sound": len(sensors_db["sound"]),
                "presence": len(sensors_db["presence"])
            },
            "total_readings": len(sensors_db["all"])
        }
        
        if DEBUG_MODE:
            if AUTH_REQUIRED:
                print(f"[DEBUG] Requête de statut reçue de {request.remote} (utilisateur: {username})")
            else:
                print(f"[DEBUG] Requête de statut reçue de {request.remote}")
        
        return aiocoap.Message(payload=json.dumps(status_data).encode('utf-8'))


# Création du serveur sécurisé
def main():
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("coap-server").setLevel(logging.DEBUG)

    # Création du serveur
    root = resource.Site()
    
    # Ressource d'authentification
    root.add_resource(['auth'], AuthResource())
    
    # Ajout des ressources pour chaque type de capteur
    root.add_resource(['sensors', 'temperature'], SensorResource("temperature"))
    root.add_resource(['sensors', 'sound'], SensorResource("sound"))
    root.add_resource(['sensors', 'presence'], SensorResource("presence"))
    root.add_resource(['sensors'], AllSensorsResource())
    
    # Configuration et statut
    root.add_resource(['config'], ConfigResource())
    root.add_resource(['status'], StatusResource())
    
    # Démarrage du serveur
    asyncio.Task(aiocoap.Context.create_server_context(root, bind=('0.0.0.0', 5683)))
    
    print("Serveur CoAP IoT sécurisé démarré sur 0.0.0.0:5683")
    print("Endpoints disponibles:")
    print("- coap://[adresse_ip]:5683/auth (POST) - Authentification et obtention du token")
    print("- coap://[adresse_ip]:5683/sensors/temperature (GET/PUT)")
    print("- coap://[adresse_ip]:5683/sensors/sound (GET/PUT)")
    print("- coap://[adresse_ip]:5683/sensors/presence (GET/PUT)")
    print("- coap://[adresse_ip]:5683/sensors (GET)")
    print("- coap://[adresse_ip]:5683/config (GET/PUT)")
    print("- coap://[adresse_ip]:5683/status (GET)")
    print("NOTE: Toutes les ressources requièrent désormais une authentification")
    print("Pour utiliser les ressources, ajoutez '?token=<votre_token>' à l'URL")
    
    # Boucle principale
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()