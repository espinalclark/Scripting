## ＤＢＲＥＬＯＡＤ
*Este script esta echo para que pueda actualizar la base de datos, detecta algun cambio en el archivo .sql y lo importa a la base de datos, asi facilita la codificacion de la **db***

## Instalacion
```
- sudo pacman -S inotify-tools

- crear un archivo de configuracion privada para Mariadb/MySQL en ~/.my.cnf
contenido: 
[client]
user=algo <-- usuario de tu db
password=algo <-- password de tu db

- chmod +x autoreload.sh <-da permiso de ejecucion al script
- ./autorelaod.sh <-ejecuta el script
```
