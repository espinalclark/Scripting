# ad_recon.py — Active Directory Reconnaissance Tool

![ad_recon](assets/ad_recon.png)

Herramienta de reconocimiento automatizado de Active Directory. Enumera usuarios, SPNs, hosts, shares y credenciales usando `impacket` y `netexec`. Diseñada para uso en laboratorios controlados y entornos de práctica.

> ⚠️ Solo para uso en entornos autorizados. El uso no autorizado es ilegal.

---

## Features

- Validación de credenciales vía SMB (netexec)
- Enumeración de usuarios del dominio (`impacket-GetADUsers`)
- Detección de cuentas AS-REP Roastables (`GetNPUsers`)
- Detección de cuentas Kerberoastables con SPNs (`GetUserSPNs`)
- Enumeración de shares SMB en el DC
- Descubrimiento de hosts en la red interna
- Resumen final con hallazgos clave
- Exportación de reporte en `.txt` con timestamp

---

## Requirements

```bash
pip install impacket
sudo apt install netexec
```

Python 3.8+

---

## Usage

```bash
python3 ad_recon.py -d <domain> -u <user> -p <password> -dc <DC_IP> [-o]
```

| Flag | Descripción |
|------|-------------|
| `-d` | Dominio (ej: `corp.local`) |
| `-u` | Usuario de dominio |
| `-p` | Password |
| `-dc` | IP del Domain Controller |
| `-o` | Guardar reporte en `.txt` |

---

## Examples

```bash
# Enumeración básica
python3 ad_recon.py -d corp.local -u j.smith -p Password123! -dc 10.10.10.10

# Guardar reporte
python3 ad_recon.py -d corp.local -u j.smith -p Password123! -dc 10.10.10.10 -o
```

---

## Output

```
  █████╗ ██████╗     ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔══██╗    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████║██║  ██║    ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██║██║  ██║    ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║██████╔╝    ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝

[*] Dominio  : corp.local
[*] Usuario  : j.smith
[*] DC       : 10.10.10.10

===================================================================
  VALIDANDO CREDENCIALES
===================================================================
[+] Credenciales validas

===================================================================
  AS-REP ROASTABLE (DONT_REQ_PREAUTH)
===================================================================
$krb5asrep$23$m.jones@CORP.LOCAL:...

===================================================================
  RESUMEN FINAL
===================================================================
  Credenciales validas : SI
  Admin detectado      : NO
  AS-REP Roastable     : SI
  Kerberoastable       : SI
```

---

## Lab Context

Desarrollado como parte del [ad-attack-lab](https://github.com/espinalclark/ad-attack-lab) — laboratorio de Active Directory con misconfigs intencionales para práctica de red teaming.

Cadena de ataque completa del lab:

```
LLMNR Poisoning → Credential Capture → Enumeration → AS-REP/Kerberoasting
→ Ligolo-ng Pivoting → ACL Abuse → ESC1 (ADCS) → DCSync → Golden Ticket
```

---

## Author

**Clark Espinal** — [@cl4rksec](https://github.com/espinalclark)

Junior Pentester | eJPT | ICCA
