#!/usr/bin/env python3

import datetime
import logging
import asyncio
import os
import json
import random
from time import time
import ssl

import aiocoap.resource as resource
import aiocoap
from aiocoap.numbers.contentformat import ContentFormat
import aiocoap.transports.tinydtls

# Configuration - Chiffrement ajouté, mais autres vulnérabilités maintenues
RESOURCE_PATH = "data_capteurs"
NO_AUTH = True  # Pas d'authentification
DEBUG_MODE = True  # Mode debug activé
ALLOW_ALL_ORIGINS = True  # CORS ouvert à tous
SECRET_KEY = "iot_master_key_123"  # Clé secrète hardcodée

# Paramètres DTLS pour chiffrement des communications
DTLS_KEY_STORE_DIR = "dtls_keys"
DTLS_PSK_KEY = b"pre-shared-key-for-dtls"  # Clé DTLS en bytes
DTLS_IDENTITY = "coap-server"

# Simulation de base de données de capteurs (en mémoire)
sensors_db = {
    "temperature": [],
    "sound": [],
    "presence": [],
    "all": []  # Pour stocker toutes les données ensemble
}

# Store de sécurité DTLS
class SimpleSecurityStore(DTLSSecurityStore):
    def _get_psk(self, host, port):
        # Retourne la clé pré-partagée pour l'authentification DTLS
        return DTLS_IDENTITY, DTLS_PSK_KEY

class SensorResource(resource.Resource):
    """Resource CoAP pour un type de capteur spécifique."""
    
    def __init__(self, sensor_type):
        super().__init__()
        self.sensor_type = sensor_type
        self.content = f"Capteur {sensor_type} pret a recevoir des donnees".encode('utf-8')
        
    async def render_get(self, request):
        # Vulnérabilité: Pas de vérification d'authentification
        if self.sensor_type in sensors_db and sensors_db[self.sensor_type]:
            # Retourne toutes les données du capteur spécifique sans filtrage
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
        
        # Log sensible avec informations clients
        if DEBUG_MODE:
            print(f"[DEBUG] Requete GET recue pour capteur {self.sensor_type} de {request.remote}")
        
        return aiocoap.Message(payload=response_json.encode('utf-8'))

    async def render_put(self, request):
        # Vulnérabilité: Pas de validation des données
        try:
            sensor_data = json.loads(request.payload.decode('utf-8'))
            
            # Vulnérabilité: Pas de validation de structure ou de valeurs
            # Ajoute un timestamp si non présent
            if "timestamp" not in sensor_data:
                sensor_data["timestamp"] = time()
                
            # Ajoute l'ID du capteur dans les données
            sensor_data["sensor_type"] = self.sensor_type
            
            # Stocke les données
            sensors_db[self.sensor_type].append(sensor_data)
            sensors_db["all"].append(sensor_data)
            
            # Vulnérabilité: Écriture dans le système de fichiers sans validation
            try:
                os.makedirs(RESOURCE_PATH, exist_ok=True)
                filename = f"{RESOURCE_PATH}/{self.sensor_type}_{datetime.datetime.now().timestamp()}.json"
                with open(filename, "w") as f:
                    json.dump(sensor_data, f)
            except Exception as e:
                print(f"Erreur d'ecriture: {e}")
            
            # Log sensible
            if DEBUG_MODE:
                print(f"[DEBUG] Donnees {self.sensor_type} recues de {request.remote}")
                print(f"[DEBUG] Contenu: {sensor_data}")
            
            response = {
                "status": "success",
                "message": f"Donnees {self.sensor_type} enregistrees avec succes",
                "data_count": len(sensors_db[self.sensor_type])
            }
            
            return aiocoap.Message(code=aiocoap.CHANGED, payload=json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=b"Format JSON invalide")
        except Exception as e:
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR, payload=str(e).encode('utf-8'))


class AllSensorsResource(resource.Resource):
    """Resource pour accéder à toutes les données des capteurs."""
    
    async def render_get(self, request):
        # Vulnérabilité: Retourne toutes les données sans filtrage ni pagination
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
        
        # Log sensible
        if DEBUG_MODE:
            print(f"[DEBUG] Requete GET pour tous les capteurs de {request.remote}")
        
        return aiocoap.Message(payload=json.dumps(response_data).encode('utf-8'))


class ConfigResource(resource.Resource):
    """Resource pour la configuration du système de capteurs."""
    
    def __init__(self):
        super().__init__()
        # Vulnérabilité: Configuration sensible en clair
        self.config = {
            "sampling_rate": 5,  # secondes
            "alert_threshold": {
                "temperature": {"min": 15, "max": 30},
                "sound": {"min": 0, "max": 100},
                "presence": {"sensitivity": "high"}
            },
            "admin_password": "admin123",  # Mot de passe en clair
            "master_key": SECRET_KEY,
            "backup_server": "192.168.1.100",
            "debug_mode": DEBUG_MODE
        }
        
    async def render_get(self, request):
        # Vulnérabilité: Retourne la configuration complète y compris les informations sensibles
        return aiocoap.Message(payload=json.dumps(self.config).encode('utf-8'))
        
    async def render_put(self, request):
        # Vulnérabilité: Permet de modifier la configuration sans authentification
        try:
            new_config = json.loads(request.payload.decode('utf-8'))
            
            # Vulnérabilité: Mise à jour sans validation
            self.config.update(new_config)
            
            # Log sensible
            if DEBUG_MODE:
                print(f"[DEBUG] Configuration mise a jour par {request.remote}")
                print(f"[DEBUG] Nouvelle config: {self.config}")
            
            return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Configuration mise a jour")
        except Exception as e:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=str(e).encode('utf-8'))


class CommandResource(resource.Resource):
    """Ressource permettant l'exécution de commandes système (très vulnérable)."""
    
    async def render_post(self, request):
        # Vulnérabilité critique: Exécution de commande sans validation
        try:
            command = request.payload.decode('utf-8')
            if DEBUG_MODE:
                print(f"[DEBUG] Commande recue: {command}")
            
            # Injection de commande directe
            result = os.popen(command).read()
            
            return aiocoap.Message(payload=result.encode('utf-8'))
        except Exception as e:
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR, payload=str(e).encode('utf-8'))


# Création et configuration des certificats pour DTLS
def setup_dtls_credentials():
    # Crée un répertoire pour stocker les clés et certificats si nécessaire
    os.makedirs(DTLS_KEY_STORE_DIR, exist_ok=True)
    
    # Ici nous utilisons une clé pré-partagée (PSK) 
    # La configuration est gérée par SimpleSecurityStore
    
    print("[+] Configuration DTLS établie avec clé pré-partagée")


# Création du serveur sécurisé avec DTLS
async def create_server():
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("coap-server").setLevel(logging.DEBUG)

    # Configuration DTLS
    setup_dtls_credentials()
    
    # Création du serveur
    root = resource.Site()
    
    # Ajout des ressources pour chaque type de capteur
    root.add_resource(['sensors', 'temperature'], SensorResource("temperature"))
    root.add_resource(['sensors', 'sound'], SensorResource("sound"))
    root.add_resource(['sensors', 'presence'], SensorResource("presence"))
    root.add_resource(['sensors'], AllSensorsResource())
    
    # Configuration et commandes
    root.add_resource(['config'], ConfigResource())
    root.add_resource(['command'], CommandResource())
    
    # Création du contexte serveur avec DTLS
    context = await aiocoap.Context.create_server_context(
        root, 
        bind=('0.0.0.0', 5684),  # Port standard pour CoAPS (CoAP sur DTLS)
        server_credentials=SimpleSecurityStore()
    )
    
    # Création d'un contexte non-DTLS pour rétrocompatibilité (optionnel)
    context_insecure = await aiocoap.Context.create_server_context(
        root,
        bind=('0.0.0.0', 5683)  # Port standard pour CoAP non sécurisé
    )
    
    print("Serveur CoAP IoT démarré:")
    print("- Port sécurisé (DTLS): coaps://[adresse_ip]:5684/")
    print("- Port non-sécurisé: coap://[adresse_ip]:5683/ (pour rétrocompatibilité)")
    print("\nEndpoints disponibles:")
    print("- {proto}://[adresse_ip]:{port}/sensors/temperature (GET/PUT)")
    print("- {proto}://[adresse_ip]:{port}/sensors/sound (GET/PUT)")
    print("- {proto}://[adresse_ip]:{port}/sensors/presence (GET/PUT)")
    print("- {proto}://[adresse_ip]:{port}/sensors (GET)")
    print("- {proto}://[adresse_ip]:{port}/config (GET/PUT)")
    print("- {proto}://[adresse_ip]:{port}/command (POST)")
    print("\nATTENTION: Ce serveur utilise maintenant DTLS pour le chiffrement,")
    print("mais contient toujours d'autres vulnérabilités !")
    print("Pour sécurité maximale, désactivez le port non-sécurisé (5683)")


def main():
    loop = asyncio.get_event_loop()
    loop.create_task(create_server())
    loop.run_forever()


if __name__ == "__main__":
    main()