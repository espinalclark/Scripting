===================
portscan.sh - README
===================

Uso:
 ./portscan.sh <IP> <PORT_START> <PORT_END> <THREADS> <OUTPUT.txt>

Ejemplo:
 ./portscan.sh 192.168.1.10 1 100 50 resultados.txt

Qué hace:
 - Escanea puertos en paralelo usando /dev/tcp
 - Detecta puertos abiertos
 - Intenta obtener banner con nc
 - Guarda resultados en el archivo indicado

Requisitos:
 - bash
 - nc
 - timeout

Salida:
 - Muestra puertos abiertos en pantalla
 - Guarda: "Puerto X abierto - banner" en OUTPUT.txt

