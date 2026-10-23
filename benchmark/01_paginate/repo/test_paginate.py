from paginate import page_count, paginate

ITEMS = list(range(1, 11))  # [1, 2, ..., 10]


def test_first_page():
    assert paginate(ITEMS, 1, 3) == [1, 2, 3]


def test_middle_page():
    assert paginate(ITEMS, 2, 3) == [4, 5, 6]


def test_last_partial_page():
    assert paginate(ITEMS, 4, 3) == [10]


def test_page_after_end_is_empty():
    assert paginate(ITEMS, 5, 3) == []


def test_page_count():
    assert page_count(ITEMS, 3) == 4
    assert page_count([], 3) == 0
