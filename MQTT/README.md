# Lancer plusieurs scripts en simultané

```bash
for i in {1..20}; do python3 mqtt_dos.py & done
```

Avec cette commande, on lance 20 instances du script `mqtt_dos.py` en parallèle. Cela permet de simuler un grand nombre de connexions simultanées au serveur MQTT, ce qui peut saturer le serveur et provoquer un déni de service.

--- 

Cette attaque se base sur la CVE-2021-41039.

https://nvd.nist.gov/vuln/detail/CVE-2021-41039