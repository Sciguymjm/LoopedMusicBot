import json
import os


def load_json(fn, default=None):
    if default is None:
        default = {}
    if not os.path.isfile(fn):
        with open(fn, 'w') as f:
            json.dump(default, f)
    with open(fn) as f:
        return json.load(f)


def save_json(obj, fn):
    with open(fn, 'w') as f:
        json.dump(obj, f)
