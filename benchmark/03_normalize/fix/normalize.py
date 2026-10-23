def normalize(values):
    """Scale values linearly to [0, 1]: the minimum becomes 0.0, the maximum 1.0.

    If all values are equal, return a list of 0.0.
    An empty input returns an empty list.
    """
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]
