#!/usr/bin/env python3
"""
send_algo_with_protected_wallet.py
Versión del script que permite:
 - Crear una wallet (mostrar mnemonic)
 - Usar una mnemonic pegada
 - Guardar la mnemonic cifrada con contraseña al momento de ejecutar
 - Cargar wallet desde archivo cifrado (solicita contraseña)
 - Pedir dirección destino y cantidad, y enviar ALGO (TestNet)

Requisitos:
 pip install py-algorand-sdk pycryptodome
"""
import os
import sys
import json
import base64
from getpass import getpass
from typing import Tuple, Optional

from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod

# Cifrado
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

# ----------------------------------------------------------------------
# Configuración de la red (TestNet)
ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"
ALGOD_TOKEN   = ""                     # algonode no necesita token
HEADERS       = {"User-Agent": "algod-python"}   # opcional

algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS, HEADERS)

# ----------------------------------------------------------------------
# Parámetros de derivación de clave
PBKDF2_ITER = 200_000  # iteraciones (más = más seguro, pero más lento)
KEY_LEN = 32  # 256 bits para AES-256-GCM

# ----------------------------------------------------------------------
def derive_key(password: str, salt: bytes) -> bytes:
    return PBKDF2(password, salt, dkLen=KEY_LEN, count=PBKDF2_ITER)

def encrypt_mnemonic(mn: str, password: str) -> dict:
    salt = get_random_bytes(16)
    key = derive_key(password, salt)
    nonce = get_random_bytes(12)  # recommended for GCM
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(mn.encode('utf-8'))
    return {
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "tag": base64.b64encode(tag).decode(),
        "ciphertext": base64.b64encode(ct).decode()
    }

def decrypt_mnemonic(blob: dict, password: str) -> Optional[str]:
    try:
        salt = base64.b64decode(blob["salt"])
        nonce = base64.b64decode(blob["nonce"])
        tag = base64.b64decode(blob["tag"])
        ct = base64.b64decode(blob["ciphertext"])
        key = derive_key(password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        mn = cipher.decrypt_and_verify(ct, tag)
        return mn.decode('utf-8')
    except Exception as e:
        return None

def save_encrypted_wallet_file(path: str, address: str, enc_blob: dict) -> None:
    data = {
        "address": address,
        "encrypted_mnemonic": enc_blob
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    # restringir permisos en sistemas tipo unix
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass

def load_encrypted_wallet_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------------------------------------------------
# Funciones Algorand (tu código original adaptado)
def crear_cuenta() -> Tuple[str, str, str]:
    private_key, address = account.generate_account()
    passphrase = mnemonic.from_private_key(private_key)
    print("\n=== NUEVA CUENTA ===")
    print(f"Dirección : {address}")
    print(f"Frase mnemónica (guárdala bien):\n{passphrase}\n")
    return private_key, address, passphrase

def cuenta_desde_mnemonic(mn: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        sk = mnemonic.to_private_key(mn)
        addr = account.address_from_private_key(sk)
        return sk, addr
    except Exception as e:
        print("Error: mnemonic inválida o formato incorrecto.", e)
        return None, None

def obtener_saldo(address: str) -> int:
    acct_info = algod_client.account_info(address)
    micro_algo = acct_info.get('amount', 0)
    algo = micro_algo / 1_000_000
    print(f"Saldo de {address[:6]}... : {algo} ALGO")
    return micro_algo

def enviar_algo(sender_sk: str, sender_addr: str, receiver_addr: str, amount_micro: int):
    params = algod_client.suggested_params()
    unsigned_txn = transaction.PaymentTxn(
        sender=sender_addr,
        sp=params,
        receiver=receiver_addr,
        amt=amount_micro,
        note=b"Demo Algorand"
    )
    signed_txn = unsigned_txn.sign(sender_sk)
    txid = algod_client.send_transaction(signed_txn)
    print(f"\nTransacción enviada, ID: {txid}")
    try:
        confirmed_txn = transaction.wait_for_confirmation(algod_client, txid, 10)
        print("✅ Confirmada en el bloque:", confirmed_txn.get('confirmed-round'))
        return confirmed_txn
    except Exception as e:
        print("⚠️ Error esperando confirmación:", e)
        return None

# ----------------------------------------------------------------------
# Interfaz para cargar/crear wallet con protección por contraseña
def seleccionar_o_cargar_wallet() -> Tuple[str, str]:
    """
    Opciones:
     1) Crear nueva wallet y opcionalmente guardarla cifrada ahora.
     2) Pegar mnemonic (no guardada).
     3) Cargar wallet cifrada desde archivo (.json) (se pide contraseña).
    Devuelve (sender_sk, sender_addr)
    """
    print("Elige opción para la wallet emisora:")
    print("  1) Crear nueva wallet (mostrar mnemonic) ")
    print("  2) Pegar mnemonic existente (copiar desde Enpass)")
    print("  3) Cargar wallet protegida desde archivo (guardada previamente)")

    choice = input("Opción (1/2/3): ").strip()
    if choice == "1":
        sk, addr, passphrase = crear_cuenta()
        # preguntar si desea guardar cifrada ahora
        save_choice = input("¿Deseas guardar esta wallet cifrada con contraseña? (s/N): ").strip().lower()
        if save_choice == "s":
            path = input("Ruta de archivo para guardar (ej. mywallet.json): ").strip() or "mywallet.json"
            pwd = getpass("Elige una contraseña segura para proteger la wallet: ")
            pwd_confirm = getpass("Confirma la contraseña: ")
            if pwd != pwd_confirm:
                print("Contraseñas no coinciden. No se guardó el archivo.")
            else:
                enc = encrypt_mnemonic(passphrase, pwd)
                save_encrypted_wallet_file(path, addr, enc)
                print(f"Wallet guardada cifrada en: {path}")
        return sk, addr

    elif choice == "2":
        mn = getpass("Pega aquí la mnemonic (input oculto): ").strip()
        if not mn:
            print("No ingresaste mnemonic. Abortando.")
            sys.exit(1)
        sk, addr = cuenta_desde_mnemonic(mn)
        if sk is None:
            print("Mnemonic inválida. Abortando.")
            sys.exit(1)
        # preguntar si desea guardar cifrada
        save_choice = input("¿Deseas guardar esta mnemonic cifrada con contraseña? (s/N): ").strip().lower()
        if save_choice == "s":
            path = input("Ruta de archivo para guardar (ej. mywallet.json): ").strip() or "mywallet.json"
            pwd = getpass("Elige una contraseña segura para proteger la wallet: ")
            pwd_confirm = getpass("Confirma la contraseña: ")
            if pwd != pwd_confirm:
                print("Contraseñas no coinciden. No se guardó el archivo.")
            else:
                enc = encrypt_mnemonic(mn, pwd)
                save_encrypted_wallet_file(path, addr, enc)
                print(f"Wallet guardada cifrada en: {path}")
        return sk, addr

    elif choice == "3":
        path = input("Ruta del archivo cifrado (ej. mywallet.json): ").strip()
        if not path or not os.path.isfile(path):
            print("Archivo no encontrado. Abortando.")
            sys.exit(1)
        data = load_encrypted_wallet_file(path)
        addr_stored = data.get("address")
        blob = data.get("encrypted_mnemonic")
        pwd = getpass(f"Introduce la contraseña para desbloquear la wallet {addr_stored}: ")
        mn = decrypt_mnemonic(blob, pwd)
        if mn is None:
            print("Contraseña incorrecta o archivo corrupto. Abortando.")
            sys.exit(1)
        sk, addr = cuenta_desde_mnemonic(mn)
        if sk is None:
            print("No se pudo derivar la cuenta desde la mnemonic descifrada. Abortando.")
            sys.exit(1)
        print(f"Wallet cargada: {addr}")
        return sk, addr
    else:
        print("Opción inválida. Intenta de nuevo.")
        return seleccionar_o_cargar_wallet()

# ----------------------------------------------------------------------
def main():
    print("=== Script interactivo con wallet protegida (Algorand TestNet) ===\n")

    sender_sk, sender_addr = seleccionar_o_cargar_wallet()

    print("\nSaldo inicial de la cuenta emisora:")
    try:
        obtener_saldo(sender_addr)
    except Exception as e:
        print("No se pudo consultar el saldo. Verifica la conexión a TestNet.", e)

    input("\nPresiona ENTER después de haber recibido fondos de la faucet (si aplica)...")

    print("\nSaldo actualizado:")
    obtener_saldo(sender_addr)

    # Pedir wallet destino
    receiver_addr = input("\nIngresa la dirección de la wallet destino: ").strip()
    if not receiver_addr:
        print("No ingresaste la dirección destino. Abortando.")
        sys.exit(1)

    # Pedir cantidad
    amount_algo = input("Cantidad a enviar (en ALGO, ejemplo: 0.1): ").strip()
    try:
        amount_micro = int(float(amount_algo) * 1_000_000)
        if amount_micro <= 0:
            raise ValueError()
    except Exception:
        print("Cantidad inválida. Abortando.")
        sys.exit(1)

    # Confirmación
    print("\nResumen de la transferencia:")
    print(f"  Emisor : {sender_addr}")
    print(f"  Receptor: {receiver_addr}")
    print(f"  Monto  : {amount_algo} ALGO ({amount_micro} microALGO)")
    yn = input("¿Confirmas enviar? (s/N): ").strip().lower()
    if yn != "s":
        print("Transferencia cancelada por el usuario.")
        return

    # Enviar
    confirmed = enviar_algo(sender_sk, sender_addr, receiver_addr, amount_micro)
    if confirmed:
        print("\n=== Saldos finales ===")
        obtener_saldo(sender_addr)
        obtener_saldo(receiver_addr)
    else:
        print("La transacción no se confirmó. Revisa el ID o los errores mostrados.")

if __name__ == "__main__":
    main()