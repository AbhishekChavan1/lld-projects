from services.atmservices import ATMService  # noqa: E402


def main():
    service = ATMService()

    account = service.create_account("AC1001", "Alice", balance=5000)
    service.issue_card("Alice", "4000000000000001", "1234", account)

    account2 = service.create_account("AC1002", "Bob", balance=1000)
    service.issue_card("Bob", "4000000000000002", "4321", account2)

    print("=== Alice's session ===")
    atm = service.create_session("4000000000000001")
    try:
        atm.authenticate("9999")  # wrong PIN
    except ValueError as error:
        print(f"Wrong PIN rejected: {error}")
    atm.authenticate("1234")  # correct PIN

    print(f"Balance: INR {atm.check_balance():,}")
    notes = atm.withdraw(1350)
    print(f"Withdrew INR 1,350 -> {', '.join(f'{c}x{d}' for d, c in notes.items())}")
    print(f"Balance after withdrawal: INR {atm.check_balance():,}")

    atm.deposit(500)
    print(f"Balance after deposit: INR {atm.check_balance():,}")

    atm.change_pin("1234", "5678")
    print("PIN changed successfully")

    print("\nTransaction history:")
    for transaction in atm.get_transactions():
        print(f"  {transaction}")

    atm.eject_card()
    print("\nCard ejected. ATM state:", atm.state)

    print("\n=== Bob's blocked-card flow ===")
    atm2 = service.create_session("4000000000000002")
    for attempt in range(3):
        try:
            atm2.authenticate("0000")
        except ValueError as error:
            print(f"  Attempt {attempt + 1}: {error}")
    print("  Card blocked:", service.bank.get_card("4000000000000002").is_blocked)


if __name__ == "__main__":
    main()
