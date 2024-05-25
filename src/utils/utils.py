def masked_print(value: str) -> str:
    symbols_to_mask = int(0.8 * len(value))
    return value[:-symbols_to_mask] + 'X' * symbols_to_mask
