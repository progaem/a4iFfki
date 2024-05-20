import os


def load_config():
    with open('../devo.conf', 'r') as conf_file:
        for line in conf_file:
            line = line.strip()
            if line and line[0] == '#':
                continue
            if line:
                key, value = line.split('=')
                os.environ[key] = value


def masked_print(value: str) -> str:
    symbols_to_mask = int(0.8 * len(value))
    return value[:-symbols_to_mask] + 'X' * symbols_to_mask
