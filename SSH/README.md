# Envoie massif de requêtes SYN

```bash
sudo hping3 -S -p 22 --flood <adresse_IP_de_la_cible>
```

# Contre-mesures

## 1. Activation des SYN cookies

```bash
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 1024
net.ipv4.conf.all.rp_filter = 1
```

Il faut ensuite recharger la configuration du noyau :

```bash
sudo sysctl -p
```

## 2. Règles iptables

```bash
iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP
```

Permet de filtrer les paquets SYN en limitant le nombre de connexions simultanées à 1 par seconde. Tolère des rafales de 3 paquets SYN avant de commencer à bloquer les paquets SYN supplémentaires.