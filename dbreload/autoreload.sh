#!/bin/bash
# 👾 https://github.com/espinalclark 👾#

# -------------------------------
# 🔥 AUTORELOAD SQL FOR MARIADB 🔥
# -------------------------------

FILE="archivo.sql" # <-- archivo.sql
DB="database"    #<-- name_dabatabse 

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Archivo monitoreado: $FILE"

inotifywait -m \
    -e modify \
    -e close_write \
    -e moved_to \
    -e move_self \
    -e create \
    -e delete \
    "$(dirname "$FILE")" | while read path action file; do

    if [[ "$file" == "$(basename "$FILE")" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Se detecto un cambio ($action) en $file → Importando..."

        mariadb "$DB" < "$FILE" 2>/tmp/mariadb_error.log

        if [[ $? -eq 0 ]]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] [OK] Base de datos importado."
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] Error al importar"
        fi
    fi
done

