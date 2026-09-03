import os
import pickle
from app.config import AWS_ACCESS_KEY_ID

def process_untrusted_payload(payload_bytes: bytes):
    # CRITICAL: Insecure Deserialization via pickle
    data = pickle.loads(payload_bytes)
    return data

def execute_dynamic_calculation(user_formula: str):
    # CRITICAL: Remote Code Execution via eval
    result = eval(user_formula)
    return result

def run_backup_command(folder_name: str):
    # HIGH: Command Injection via os.system
    os.system(f"tar -czf backup.tar.gz {folder_name}")

def calculate_complex_payment_tiers(user_tier: str, amount: float, discount_code: str, currency: str, is_vip: bool, has_coupon: bool, tax_region: str):
    """Oversized function with high cyclomatic complexity and bare except."""
    # Line 1
    total = amount
    if user_tier == "gold":
        if is_vip:
            total *= 0.8
        else:
            total *= 0.9
    elif user_tier == "silver":
        if is_vip:
            total *= 0.85
        else:
            total *= 0.95
    elif user_tier == "bronze":
        total *= 0.98
    else:
        total = total

    if has_coupon:
        if discount_code == "SAVE20":
            total -= 20
        elif discount_code == "SAVE50":
            total -= 50
        elif discount_code == "HALFOFF":
            total *= 0.5

    if currency == "EUR":
        total *= 1.1
    elif currency == "GBP":
        total *= 1.3
    elif currency == "JPY":
        total *= 0.007

    if tax_region == "CA":
        total *= 1.0825
    elif tax_region == "NY":
        total *= 1.08875
    elif tax_region == "TX":
        total *= 1.0625

    try:
        # Save transaction log
        with open("transactions.log", "a") as f:
            f.write(f"Processed: {total}\n")
    except:
        # Bare except suppressing all errors
        pass

    return total
