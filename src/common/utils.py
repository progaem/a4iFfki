"""
Utils module
"""
def masked_print(value: str) -> str:
    """Masks 80% of the values characters as X"""
    symbols_to_mask = int(0.8 * len(value))
    return value[:-symbols_to_mask] + 'X' * symbols_to_mask

def by_chunk(items, chunk_size=1000):
    """
    Separate iterable objects by chunks

    For example:
    >>> by_chunk([1, 2, 3, 4, 5], chunk_size=2)
    >>> [[1, 2], [3, 4], [5]]

    Parameters
    ----------
    chunk_size: int
    items: Iterable

    Returns
    -------
    List
    """
    bucket = []
    for item in items:
        if len(bucket) >= chunk_size:
            yield bucket
            bucket = []
        bucket.append(item)
    yield bucket
