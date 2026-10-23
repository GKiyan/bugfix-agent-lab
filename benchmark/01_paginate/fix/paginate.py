def paginate(items, page, page_size):
    """Return the items shown on `page`. Pages are numbered from 1."""
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


def page_count(items, page_size):
    """Number of pages needed to show all items."""
    return (len(items) + page_size - 1) // page_size
