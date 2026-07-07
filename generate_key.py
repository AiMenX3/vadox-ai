"""
Vadox Key Generator — nur für interne Entwickler-Testkeys.
Echte Kunden-Keys werden ausschliesslich vom Lizenz-Server ausgestellt
(server/vadox-license-worker/), nicht mehr hier.

Aufruf: VADOX_DEV_SECRET=<dein-dev-secret> python generate_key.py
"""

from vadox.core.license import generate_key


def main():
    print("\n=== VADOX KEY GENERATOR (nur Entwickler-Testkeys) ===\n")
    print("Paket wählen:")
    print("  1 = PRO Lifetime (197 EUR)")
    print("  2 = BUSINESS Lifetime (1.497 EUR)")
    print("  3 = Developer / Test-Key")
    print("  4 = 1 Monat (67 EUR)")

    choice = input("\nWahl [1/2/3/4]: ").strip()
    email  = input("E-Mail des Kunden (leer = anonym): ").strip()

    if choice == "2":
        key  = generate_key(customer_email=email, key_type="BUSINESS")
        typ  = "BUSINESS Lifetime"
    elif choice == "4":
        key  = generate_key(customer_email=email, key_type="MONTH")
        typ  = "1 Monat"
    else:
        key  = generate_key(customer_email=email, key_type="PRO")
        typ  = "PRO Lifetime" if choice == "1" else "Developer"

    print(f"\n  {typ} Key:")
    print(f"\n  {key}\n")
    if email:
        print(f"  Fuer: {email}")
    print("  Dieser Key ist HMAC-signiert und faelschungssicher.\n")


if __name__ == "__main__":
    main()
