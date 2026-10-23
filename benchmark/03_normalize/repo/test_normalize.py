from normalize import normalize


def test_basic():
    assert normalize([0, 5, 10]) == [0.0, 0.5, 1.0]


def test_negative_values():
    assert normalize([-10, 0, 10]) == [0.0, 0.5, 1.0]


def test_all_equal():
    assert normalize([5, 5, 5]) == [0.0, 0.0, 0.0]


def test_single_value():
    assert normalize([42]) == [0.0]


def test_empty():
    assert normalize([]) == []
