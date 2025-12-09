#!/bin/bash
echo " SCRIPT DE BUSQUEDA DE ARCHIVO "
read -p "Que archivo quieres buscar? : " file
ruta=$(find / -type f -iname "$file" 2> /dev/null)
echo "tu ruta esta en : $ruta"
