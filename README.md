# Analyse et Renforcement de la Sécurité d'un Réseau IoT Domestique

## Contexte du projet

Ce projet a été réalisé dans le cadre d'un cours de sécurité IoT à l'Université du Québec à Chicoutimi (UQAC). Notre objectif était d'analyser les vulnérabilités potentielles d'un réseau IoT domestique et de proposer des méthodes concrètes pour renforcer sa sécurité. Ce travail combine recherche théorique et applications pratiques pour évaluer et améliorer la posture de sécurité des objets connectés.

## Structure du projet
Notre projet est organisé en plusieurs modules, chacun ciblant un aspect spécifique de la sécurité IoT :

WIFI/ : Analyse et exploitation des réseaux WiFi, capture de handshakes et techniques de cracking
SSH/ : Tests de déni de service et contre-mesures pour les connexions SSH
MQTT/ : Analyse de vulnérabilités du protocole MQTT, notamment des tests DoS
COAP/ : Implémentation de serveurs CoAP avec différents niveaux de sécurité
BLE/ : Exploration et analyse de sécurité des appareils Bluetooth Low Energy

## Méthodologie
Notre approche s'est articulée autour de plusieurs phases distinctes :

1. Cartographie du réseau : Identification des appareils IoT et analyse de la topologie réseau
2. Analyse des protocoles : Étude des protocoles de communication utilisés (WiFi, MQTT, CoAP, BLE)
3. Tests d'intrusion : Simulation d'attaques pour identifier les vulnérabilités
4. Développement de contre-mesures : Implémentation de solutions pour renforcer la sécurité
5. Validation : Tests de vérification de l'efficacité des mesures de protection

## Principales vulnérabilités étudiées

Réseau WiFi
- Capture de handshakes WPA et attaques par dictionnaire
- Méthodes de déconnexion de clients légitimes

Services de connexion distante (SSH)
- Attaques par déni de service avec envoi massif de requêtes SYN
- Implémentation de contre-mesures avec SYN cookies et règles iptables

Protocole MQTT
- Exploitation de la CVE-2021-41039 pour des attaques DoS
- Saturation du serveur MQTT avec de multiples connexions parallèles

Protocole CoAP
- Développement de trois versions d'un serveur CoAP :
    - Version vulnérable avec injection de commandes
    - Version intermédiaire avec chiffrement DTLS
    - Version sécurisée avec authentification par jetons

Bluetooth Low Energy (BLE)
- Analyse des mécanismes d'authentification
- Tests de lecture/écriture sur les caractéristiques BLE
- Exploration des limitations de sécurité des appareils BLE grand public

## Outils et technologies utilisés

- Analyse réseau : Wireshark, Aircrack-ng, hping3
- Développement : Python, Arduino
- Protocoles IoT : MQTT, CoAP, BLE
- Bibliothèques : aiocoap, paho-mqtt, bleak, ArduinoBLE
- Matériel : Raspberry Pi 3, carte Arduino MKR WIFI 1010, écran LCD Shield Adafruit

## Avertissement éthique

Ce projet a été développé uniquement à des fins éducatives dans un cadre universitaire. Les techniques et outils présentés doivent être utilisés de manière responsable et éthique, uniquement sur des réseaux et appareils vous appartenant ou pour lesquels vous avez explicitement reçu l'autorisation de test.

## Conclusions principales
Nos recherches ont mis en évidence que :

1. De nombreux appareils IoT grand public présentent des vulnérabilités significatives
2. La sécurité par couches (défense en profondeur) est essentielle pour les réseaux IoT
3. La segmentation réseau constitue une approche efficace pour limiter l'impact des compromissions
4. L'authentification forte et le chiffrement des communications sont indispensables
5. La mise à jour régulière des firmwares et logiciels est critique pour la sécurité à long terme

## Contributeurs
Ce projet a été réalisé par Clément MARY, Thomas FRIDBLATT et Eliséo CHAUSSOY du cours de sécurité IoT à l'UQAC.

## Licence
Ce projet est disponible sous licence MIT. Voir le fichier LICENSE pour plus de détails.