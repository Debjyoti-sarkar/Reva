"""
NexaVault Trading Vault - PyTeal Smart Contract
================================================
Autonomous trading vault smart contract for Algorand testnet.
Handles fund custody and enforces price-based trading conditions.

Deploy via: scripts/deploy_contract.py
"""

from pyteal import (
    Approve, Bytes, Cond, Err, Global, Int, Mode,
    Reject, Seq, Assert, App, Txn,
    compileTeal, Btoi, Len, Concat, Log, And, Or,
    TxnType, InnerTxnBuilder, TxnField, InnerTxn,
    ScratchVar, TealType, If, Not, Balance, Addr
)


# ─────────────────────────────────────────────
# Global State Schema
# ─────────────────────────────────────────────
# buy_price  : uint  – price threshold to trigger a buy
# sell_price : uint  – price threshold to trigger a sell
# owner      : bytes – creator / vault controller
# last_action: bytes – "buy" | "sell" | "hold"
# last_price : uint  – last recorded price (in microALGO or USD cents)
# trade_count: uint  – number of completed trades

NUM_GLOBAL_INTS = 4   # buy_price, sell_price, last_price, trade_count
NUM_GLOBAL_BYTES = 2  # owner, last_action
NUM_LOCAL_INTS = 0
NUM_LOCAL_BYTES = 0


# ─────────────────────────────────────────────
# Helper: Global state keys
# ─────────────────────────────────────────────
KEY_BUY_PRICE   = Bytes("buy_price")
KEY_SELL_PRICE  = Bytes("sell_price")
KEY_OWNER       = Bytes("owner")
KEY_LAST_ACTION = Bytes("last_action")
KEY_LAST_PRICE  = Bytes("last_price")
KEY_TRADE_COUNT = Bytes("trade_count")


def approval_program():
    """
    Main approval program for the NexaVault trading vault.

    Handles 5 operations (passed as first app argument):
      - "create"  : initialise global state on deployment
      - "update"  : update buy/sell thresholds (owner only)
      - "trade"   : evaluate current price → approve or reject trade
      - "deposit" : accept ALGO deposits into the vault
      - "withdraw": allow owner to withdraw ALGO from vault
    """

    # ── Scratch vars ──────────────────────────────────────────────────────
    current_price  = ScratchVar(TealType.uint64)
    action_result  = ScratchVar(TealType.bytes)

    # ── Re-usable guards ──────────────────────────────────────────────────
    is_owner = Txn.sender() == App.globalGet(KEY_OWNER)
    is_creator = Txn.sender() == Global.creator_address()

    # ── On Create ─────────────────────────────────────────────────────────
    on_create = Seq(
        # Initialise all global state
        App.globalPut(KEY_OWNER,       Txn.sender()),
        App.globalPut(KEY_BUY_PRICE,   Int(150_000_000)),   # $150 (in USD cents × 1000)
        App.globalPut(KEY_SELL_PRICE,  Int(200_000_000)),   # $200
        App.globalPut(KEY_LAST_ACTION, Bytes("none")),
        App.globalPut(KEY_LAST_PRICE,  Int(0)),
        App.globalPut(KEY_TRADE_COUNT, Int(0)),
        Log(Bytes("NexaVault: vault created")),
        Approve(),
    )

    # ── Update thresholds (owner-gated) ───────────────────────────────────
    on_update_thresholds = Seq(
        Assert(is_owner),                                    # Only owner may update
        Assert(Txn.application_args.length() == Int(3)),     # op, buy, sell
        App.globalPut(KEY_BUY_PRICE,  Btoi(Txn.application_args[1])),
        App.globalPut(KEY_SELL_PRICE, Btoi(Txn.application_args[2])),
        Log(Bytes("NexaVault: thresholds updated")),
        Approve(),
    )

    # ── Trade evaluation logic ─────────────────────────────────────────────
    # Expects: args[0]="trade", args[1]=current_price_as_uint64_bytes
    on_trade = Seq(
        Assert(is_owner),                                    # AI agent backend must be owner
        Assert(Txn.application_args.length() == Int(2)),     # op + price

        # Store the incoming price
        current_price.store(Btoi(Txn.application_args[1])),
        App.globalPut(KEY_LAST_PRICE, current_price.load()),

        # Evaluate buy/sell/hold
        If(
            current_price.load() <= App.globalGet(KEY_BUY_PRICE),
            Seq(
                action_result.store(Bytes("buy")),
                App.globalPut(KEY_LAST_ACTION, Bytes("buy")),
                App.globalPut(KEY_TRADE_COUNT,
                    App.globalGet(KEY_TRADE_COUNT) + Int(1)),
                Log(Concat(Bytes("NexaVault: action=buy price="),
                           Txn.application_args[1])),
            ),
            If(
                current_price.load() >= App.globalGet(KEY_SELL_PRICE),
                Seq(
                    action_result.store(Bytes("sell")),
                    App.globalPut(KEY_LAST_ACTION, Bytes("sell")),
                    App.globalPut(KEY_TRADE_COUNT,
                        App.globalGet(KEY_TRADE_COUNT) + Int(1)),
                    Log(Concat(Bytes("NexaVault: action=sell price="),
                               Txn.application_args[1])),
                ),
                Seq(
                    action_result.store(Bytes("hold")),
                    App.globalPut(KEY_LAST_ACTION, Bytes("hold")),
                    Log(Bytes("NexaVault: action=hold")),
                ),
            ),
        ),
        Approve(),
    )

    # ── Deposit: anyone may deposit ALGO ─────────────────────────────────
    on_deposit = Seq(
        Log(Bytes("NexaVault: deposit accepted")),
        Approve(),
    )

    # ── Withdraw: owner only ───────────────────────────────────────────────
    on_withdraw = Seq(
        Assert(is_owner),
        Assert(Txn.application_args.length() == Int(2)),     # op + amount
        Log(Bytes("NexaVault: withdrawal approved")),
        Approve(),
    )

    # ── Router ────────────────────────────────────────────────────────────
    router = Cond(
        [Txn.application_args[0] == Bytes("create"),   on_create],
        [Txn.application_args[0] == Bytes("update"),   on_update_thresholds],
        [Txn.application_args[0] == Bytes("trade"),    on_trade],
        [Txn.application_args[0] == Bytes("deposit"),  on_deposit],
        [Txn.application_args[0] == Bytes("withdraw"), on_withdraw],
    )

    # ── Top-level dispatch ────────────────────────────────────────────────
    program = Cond(
        # App creation (no OnCompletion, no args needed yet)
        [Txn.application_id() == Int(0), on_create],
        # Normal calls (OnCompletion.NoOp = 0)
        [Txn.on_completion() == Int(0),
         If(Txn.application_args.length() >= Int(1), router, Reject())],
        # DeleteApplication – owner only (OnCompletion.DeleteApplication = 5)
        [Txn.on_completion() == Int(5),
         Seq(Assert(is_creator), Approve())],
        # UpdateApplication – owner only (OnCompletion.UpdateApplication = 4)
        [Txn.on_completion() == Int(4),
         Seq(Assert(is_creator), Approve())],
        # Everything else → reject
        [Int(1) == Int(1), Reject()],
    )

    return program


def clear_program():
    """
    Clear state program – simply approves opt-out / clear-state calls.
    """
    return Approve()


# ─────────────────────────────────────────────
# Compile and export TEAL
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import os

    out_dir = os.path.dirname(os.path.abspath(__file__))

    approval_teal = compileTeal(
        approval_program(),
        mode=Mode.Application,
        version=6,
    )
    clear_teal = compileTeal(
        clear_program(),
        mode=Mode.Application,
        version=6,
    )

    approval_path = os.path.join(out_dir, "approval.teal")
    clear_path    = os.path.join(out_dir, "clear.teal")

    with open(approval_path, "w") as f:
        f.write(approval_teal)
    with open(clear_path, "w") as f:
        f.write(clear_teal)

    print(f"✅ approval.teal written to {approval_path}")
    print(f"✅ clear.teal    written to {clear_path}")
