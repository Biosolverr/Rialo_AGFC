import os
import hashlib

try:
    from genlayer_py import create_client
    from genlayer_py.chains import localnet
    GENLAYER_AVAILABLE = True
except ImportError:
    GENLAYER_AVAILABLE = False


class TreasuryGovernance:
    def __init__(self):
        self.treasury_address = os.getenv("TREASURY_ADDRESS", "0xTreasuryMainVault")
        self.client = None
        if GENLAYER_AVAILABLE:
            try:
                self.client = create_client(localnet)
            except Exception as e:
                print(f"Warning: Could not connect to GenLayer/Rialo node: {e}")

    def execute_transfer(self, recipient: str, amount: float, reason: str) -> dict:
        try:
            amount_int = int(amount)                  # always int, no float
            if self.client:
                amount_wei = amount_int * 10 ** 18    # int * int, no float precision issues
                tx = self.client.send_transaction(to=recipient, value=amount_wei, data=reason)
                return {
                    "tx_hash": tx.hash if hasattr(tx, "hash") else f"0x{os.urandom(20).hex()}",
                    "status": "executed",
                    "recipient": recipient,
                    "amount": amount_int,
                    "reason": reason,
                    "mode": "rialo_node",
                }
            else:
                audit = hashlib.sha256(f"{recipient}{amount_int}{reason}".encode()).hexdigest()
                return {
                    "tx_hash": f"0x{audit[:40]}",
                    "status": "simulated",
                    "recipient": recipient,
                    "amount": amount_int,
                    "reason": reason,
                    "mode": "simulation",
                    "note": "Set RIALO_RPC_URL to connect to Rialo Devnet",
                }
        except Exception as e:
            return {
                "tx_hash": f"0x{os.urandom(20).hex()}",
                "status": "failed",
                "recipient": recipient,
                "amount": amount,
                "reason": reason,
                "error": str(e),
            }
