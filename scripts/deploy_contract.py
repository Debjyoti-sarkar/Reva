"""
NexaVault – Smart Contract Deployment Script
=============================================
Compiles the PyTeal contract and deploys it to Algorand Testnet.

Usage
-----
    # Compile only (no deploy)
    python scripts/deploy_contract.py --compile-only

    # Full deploy
    python scripts/deploy_contract.py

    # Deploy with custom thresholds
    python scripts/deploy_contract.py --buy 150000000 --sell 220000000

Prerequisites
-------------
  1. pip install pyteal algosdk
  2. Set VAULT_MNEMONIC or VAULT_PRIVATE_KEY env var
  3. Fund the deployer account on Testnet:
       https://bank.testnet.algorand.network/

After deployment, copy the printed APP_ID into config/settings.py
or your .env file:  APP_ID=<returned_value>
"""

import argparse
import base64
import os
import sys

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod

from config.settings import ALGOD_URL, ALGOD_TOKEN
from contracts.trading_vault import approval_program, clear_program

try:
    from pyteal import compileTeal, Mode
    PYTEAL_OK = True
except ImportError:
    PYTEAL_OK = False


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def get_client() -> algod.AlgodClient:
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)


def get_deployer():
    """Load the deployer key from env."""
    mnemo = os.getenv("VAULT_MNEMONIC", "").strip()
    if mnemo:
        pk   = mnemonic.to_private_key(mnemo)
        addr = account.address_from_private_key(pk)
        return addr, pk

    raw = os.getenv("VAULT_PRIVATE_KEY", "").strip()
    if raw:
        addr = account.address_from_private_key(raw)
        return addr, raw

    raise ValueError(
        "Set VAULT_MNEMONIC or VAULT_PRIVATE_KEY environment variable "
        "to a funded Algorand Testnet account before deploying."
    )


def compile_teal_program(client: algod.AlgodClient, source: str) -> bytes:
    """Compile a TEAL program string via the algod API and return raw bytes."""
    compile_response = client.compile(source)
    return base64.b64decode(compile_response["result"])


def compile_contracts(out_dir: str) -> tuple[bytes, bytes]:
    """
    Compile approval + clear programs.

    Returns:
        (approval_bytes, clear_bytes)
    """
    if not PYTEAL_OK:
        raise ImportError("pyteal is not installed – run: pip install pyteal")

    print("🔧 Compiling PyTeal → TEAL ...")
    approval_teal = compileTeal(approval_program(), mode=Mode.Application, version=6)
    clear_teal    = compileTeal(clear_program(),    mode=Mode.Application, version=6)

    # Write TEAL files
    with open(os.path.join(out_dir, "approval.teal"), "w") as f:
        f.write(approval_teal)
    with open(os.path.join(out_dir, "clear.teal"), "w") as f:
        f.write(clear_teal)
    print("✅ TEAL files written to contracts/")

    # Compile via algod
    client = get_client()
    print("🔧 Compiling TEAL via algod ...")
    approval_bytes = compile_teal_program(client, approval_teal)
    clear_bytes    = compile_teal_program(client, clear_teal)
    print("✅ Bytecode compiled")

    return approval_bytes, clear_bytes


def deploy(approval_bytes: bytes, clear_bytes: bytes,
           buy_threshold: int, sell_threshold: int) -> int:
    """
    Deploy the vault application to Algorand Testnet.

    Args:
        approval_bytes  : Compiled approval program bytes
        clear_bytes     : Compiled clear program bytes
        buy_threshold   : Initial buy price (on-chain integer)
        sell_threshold  : Initial sell price (on-chain integer)

    Returns:
        Deployed application ID
    """
    client      = get_client()
    addr, pk    = get_deployer()

    print(f"🚀 Deploying from {addr} ...")

    # Check balance
    info = client.account_info(addr)
    balance = info.get("amount", 0)
    print(f"💰 Account balance: {balance / 1_000_000:.4f} ALGO")
    if balance < 500_000:
        raise ValueError(
            f"Insufficient balance ({balance} µALGO). "
            "Fund the account at https://bank.testnet.algorand.network/"
        )

    sp = client.suggested_params()

    global_schema = transaction.StateSchema(num_uints=4, num_byte_slices=2)
    local_schema  = transaction.StateSchema(num_uints=0, num_byte_slices=0)

    # Initial args: "create" op (will be caught by application_id == 0 path)
    app_args = [b"create",
                buy_threshold.to_bytes(8, "big"),
                sell_threshold.to_bytes(8, "big")]

    txn = transaction.ApplicationCreateTxn(
        sender=addr,
        sp=sp,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_bytes,
        clear_program=clear_bytes,
        global_schema=global_schema,
        local_schema=local_schema,
        app_args=app_args,
        note=b"NexaVault deploy",
    )

    signed = txn.sign(pk)
    txid   = client.send_transaction(signed)
    print(f"📤 Submitted deploy txn: {txid}")

    confirmed = transaction.wait_for_confirmation(client, txid, 6)
    app_id    = confirmed["application-index"]

    print(f"\n{'='*55}")
    print(f"✅ Contract deployed successfully!")
    print(f"   APP_ID  : {app_id}")
    print(f"   TxID    : {txid}")
    print(f"   Round   : {confirmed.get('confirmed-round')}")
    print(f"{'='*55}")
    print(f"\n🔑 Add this to your .env or config/settings.py:")
    print(f"   APP_ID={app_id}")

    return app_id


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Deploy NexaVault smart contract")
    parser.add_argument("--compile-only", action="store_true",
                        help="Only compile TEAL, do not deploy")
    parser.add_argument("--buy",  type=int, default=150_000_000,
                        help="Buy threshold as on-chain integer (default 150000000 = $0.15)")
    parser.add_argument("--sell", type=int, default=220_000_000,
                        help="Sell threshold (default 220000000 = $0.22)")
    args = parser.parse_args()

    contracts_dir = os.path.join(os.path.dirname(__file__), "..", "contracts")
    approval_bytes, clear_bytes = compile_contracts(contracts_dir)

    if args.compile_only:
        print("✅ Compile-only mode – skipping deployment.")
        return

    deploy(approval_bytes, clear_bytes, args.buy, args.sell)


if __name__ == "__main__":
    main()
