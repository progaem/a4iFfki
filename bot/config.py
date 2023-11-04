import os
import configparser

def load_config():
    with open('../devo.conf', 'r') as conf_file:
        for line in conf_file:
            line = line.strip()
            if line:
                key, value = line.split('=')
                os.environ[key] = value
