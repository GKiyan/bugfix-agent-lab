def to_cents(amount):
    """Convert an amount in euros (float) to an integer number of cents."""
    return round(amount * 100)


def format_cents(cents):
    """Format a number of cents as a string like '12.05 EUR'."""
    return f"{cents // 100}.{cents % 100:02d} EUR"
