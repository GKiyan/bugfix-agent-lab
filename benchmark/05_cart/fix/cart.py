from money import format_cents, to_cents


class Cart:
    def __init__(self):
        self.items = []  # list of (name, unit_price_in_cents, quantity)

    def add(self, name, price, quantity=1):
        """Add an item. `price` is the unit price in euros (float)."""
        self.items.append((name, to_cents(price), quantity))

    def subtotal_cents(self):
        return sum(price * quantity for _, price, quantity in self.items)

    def total_cents(self, discount_percent=0):
        """Total after a discount given in percent (10 means 10%), rounded to the cent."""
        subtotal = self.subtotal_cents()
        return round(subtotal - subtotal * discount_percent / 100)

    def receipt(self, discount_percent=0):
        return "Total: " + format_cents(self.total_cents(discount_percent))
