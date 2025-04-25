# Partie BLE - Analyse de Sécurité Bluetooth Low Energy

Cette partie du projet se concentre sur l'exploration et l'analyse de sécurité des appareils Bluetooth Low Energy (BLE). Le code arduino était uploadé sur la MKR WIFI 1010 que nous avions à disposition. Nous avons utilisé un dongle USB Bluetooth pour interagir avec les appareils BLE à proximité.

## Aperçu de l'outil BLE

Notre outil de scanning BLE (`sniffingBLE.py`) permet de :

- Découvrir les appareils BLE à proximité
- Se connecter à un appareil sélectionné
- Explorer les services et caractéristiques disponibles
- Lire et écrire des valeurs dans les caractéristiques accessibles

### Limites et défis rencontrés

Notre exploration de la sécurité BLE a été limitée aux aspects suivants :

- **Découverte et authentification** : Nous avons réussi à nous connecter aux appareils et à accéder aux caractéristiques autorisées après authentification
- **Lecture/écriture** : Nous avons pu lire et écrire des valeurs aux caractéristiques lorsque les permissions le permettaient

Cependant, nous n'avons pas réussi à :
- Interrompre une connexion BLE établie entre deux appareils
- Contourner les mécanismes d'authentification pour accéder à des caractéristiques protégées
- Envoyer des données sans être authentifié au préalable
- Exécuter des attaques man-in-the-middle efficaces

### Prérequis

- Python 3.x
- Bibliothèque Bleak
- Adaptateur Bluetooth compatible avec BLE

Installation des dépendances :
```bash
pip install bleak
```

### Utilisation de l'outil BLE

Pour lancer l'outil de scanning BLE :

```bash
python sniffingBLE.py
```

L'outil fonctionne en mode interactif :

1. Il scanne d'abord les appareils BLE à proximité
2. Affiche une liste numérotée des appareils trouvés
3. Vous invite à sélectionner un appareil par son numéro
4. Explore et affiche les services et caractéristiques de l'appareil
5. Vous permet de lire ou d'écrire dans les caractéristiques sélectionnées

Pour quitter l'outil à tout moment, entrez 'exit' à l'invite.
Pour relancer un scan, entrez 'rescan'.

### Considérations de sécurité BLE

Notre exploration a mis en évidence plusieurs aspects de la sécurité BLE :

- De nombreux appareils BLE grand public implémentent correctement les mécanismes d'authentification de base
- Les caractéristiques sensibles sont généralement protégées par des mécanismes de contrôle d'accès
- Les connexions BLE modernes utilisent des méthodes de chiffrement et d'authentification qui offrent une protection raisonnable contre les attaques simples

Cependant, nous avons également observé que :
- Certains appareils exposent des informations non sensibles via des caractéristiques accessibles sans authentification
- La phase de pairing/bonding reste un moment potentiellement vulnérable dans le cycle de vie d'une connexion BLE

### Ressource supplémentaire

Au cours de notre exploration, nous avons trouvé une  vidéo un peu fantaisiste sur la vuknérabilité du BLE pour certains sextoys. Cela illustre les défis de sécurité auxquels sont confrontés les appareils connectés. Vous pouvez la visionner au lien suivant : [Potyos - J'ai hacké un s*xtoy](https://youtu.be/03puer6fnGE?si=Xw1eeRbePF3HIh36)