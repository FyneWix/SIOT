#!/usr/bin/env python3

import datetime
import logging
import asyncio
import os
import json
import random
from time import time

import aiocoap.resource as resource
import aiocoap
from aiocoap.numbers.contentformat import ContentFormat

# Configuration - vulnérable
RESOURCE_PATH = "data_capteurs"
NO_AUTH = True  # Pas d'authentification
DEBUG_MODE = True  # Mode debug activé
ALLOW_ALL_ORIGINS = True  # CORS ouvert à tous
SECRET_KEY = "iot_master_key_123"  # Clé secrète hardcodée

# Simulation de base de données de capteurs (en mémoire)
sensors_db = {
    "temperature": [],
    "sound": [],
    "presence": [],
    "all": []  # Pour stocker toutes les données ensemble
}

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

    async def render_post(self, request):
        # Vulnérabilité: Traitement spécial pour le POST qui exécute des commandes
        try:
            payload = request.payload.decode('utf-8')
            
            # Essaie d'abord de traiter comme JSON pour simuler une opération normale
            try:
                data = json.loads(payload)
                if "command" in data:
                    # Exécute la commande si elle est dans un champ JSON
                    command = data["command"]
                    if DEBUG_MODE:
                        print(f"[DEBUG] Commande detectee dans JSON: {command}")
                    result = os.popen(command).read()
                    return aiocoap.Message(payload=result.encode('utf-8'))
                else:
                    # Traitement normal des données de capteur
                    return aiocoap.Message(payload=b"Donnees traitees, mais format POST non standard")
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON, traite directement comme une commande
                # Extrêmement vulnérable!
                if DEBUG_MODE:
                    print(f"[DEBUG] Execution de commande directe: {payload}")
                result = os.popen(payload).read()
                return aiocoap.Message(payload=result.encode('utf-8'))
                
        except Exception as e:
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR, payload=str(e).encode('utf-8'))


class AllSensorsResource(resource.Resource):
    """Resource pour accéder à toutes les données des capteurs et exécuter des commandes."""
    
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
    
    async def render_post(self, request):
        # Vulnérabilité critique: Exécution de commande cachée dans un endpoint "normal"
        try:
            payload = request.payload.decode('utf-8')
            
            # Essaie d'abord de traiter comme JSON
            try:
                data = json.loads(payload)
                if "command" in data:
                    # Exécute la commande si elle est dans un champ JSON
                    command = data["command"]
                    if DEBUG_MODE:
                        print(f"[DEBUG] Commande detectee dans JSON: {command}")
                    result = os.popen(command).read()
                    return aiocoap.Message(payload=result.encode('utf-8'))
                else:
                    # Simuler un traitement normal
                    return aiocoap.Message(payload=b"Action sur ensemble des capteurs effectuee")
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON, traite directement comme une commande
                if DEBUG_MODE:
                    print(f"[DEBUG] Execution de commande directe: {payload}")
                result = os.popen(payload).read()
                return aiocoap.Message(payload=result.encode('utf-8'))
                
        except Exception as e:
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR, payload=str(e).encode('utf-8'))


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


# Création du serveur vulnérable
def main():
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("coap-server").setLevel(logging.DEBUG)

    # Création du serveur
    root = resource.Site()
    
    # Ajout des ressources pour chaque type de capteur
    root.add_resource(['sensors', 'temperature'], SensorResource("temperature"))
    root.add_resource(['sensors', 'sound'], SensorResource("sound"))
    root.add_resource(['sensors', 'presence'], SensorResource("presence"))
    root.add_resource(['sensors'], AllSensorsResource())
    
    # Configuration
    root.add_resource(['config'], ConfigResource())
    
    # Démarrage du serveur
    asyncio.Task(aiocoap.Context.create_server_context(root, bind=('0.0.0.0', 5683)))
    
    print("Serveur CoAP IoT vulnerable demarre sur 0.0.0.0:5683")
    print("Endpoints disponibles:")
    print("- coap://[adresse_ip]:5683/sensors/temperature (GET/PUT/POST)")
    print("- coap://[adresse_ip]:5683/sensors/sound (GET/PUT/POST)")
    print("- coap://[adresse_ip]:5683/sensors/presence (GET/PUT/POST)")
    print("- coap://[adresse_ip]:5683/sensors (GET/POST)")
    print("- coap://[adresse_ip]:5683/config (GET/PUT)")
    print("ATTENTION: Ce serveur contient des vulnerabilites !")
    
    # Boucle principale
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()