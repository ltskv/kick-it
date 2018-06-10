import json


def read_config():
    with open('nao_defaults.json') as f:
        cfg = json.load(f)
    return cfg
