#!/bin/bash
host=$1
p_start=$2
p_end=$3
threads=$4
outfile=$5

if [ $# -ne 5 ]; then
    echo "Uso: $0 <IP> <inicio> <fin> <hilos> <output.txt>"
    exit 1
fi

echo "Iniciando escaneo contra $host"
echo "Rango: $p_start-$p_end | Hilos: $threads"
echo "Guardando en: $outfile"
echo > "$outfile"

scan_port() {
    port=$1
    timeout 0.3 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null
    if [ $? -eq 0 ]; then
        banner=$(echo "" | timeout 0.5 nc -nv $host $port 2>/dev/null | head -n 1)
        if [ -z "$banner" ]; then banner="(sin banner)"; fi

        echo -e "\e[32m$port abierto\e[0m → $banner"
        echo "Puerto $port abierto - $banner" >> "$outfile"
    fi
}

total_ports=$((p_end - p_start + 1))
count=0

for port in $(seq $p_start $p_end); do

    while [ $(jobs -rp | wc -l) -ge $threads ]; do
        sleep 0.05
    done

    scan_port $port &

    count=$((count + 1))
    percent=$((count * 100 / total_ports))
    echo -ne "Escaneando: $percent% \r"

done

wait
echo -e "\n\nEscaneo completado."
echo "Resultados guardados en $outfile"
