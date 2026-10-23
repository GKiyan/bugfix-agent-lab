from cart import Cart


def test_price_conversion():
    cart = Cart()
    cart.add("book", 19.99)
    assert cart.subtotal_cents() == 1999


def test_quantity():
    cart = Cart()
    cart.add("pen", 1.50, quantity=3)
    assert cart.subtotal_cents() == 450


def test_no_discount():
    cart = Cart()
    cart.add("lamp", 20.00)
    assert cart.total_cents() == 2000


def test_discount():
    cart = Cart()
    cart.add("lamp", 20.00)
    assert cart.total_cents(discount_percent=10) == 1800


def test_receipt():
    cart = Cart()
    cart.add("book", 19.99)
    assert cart.receipt(discount_percent=10) == "Total: 17.99 EUR"
