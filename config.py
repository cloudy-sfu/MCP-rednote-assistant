import os
import json


def validate(config_):
    max_func_call_rounds = config_.get('max_func_call_rounds')
    if not (isinstance(max_func_call_rounds, int) and max_func_call_rounds > 0):
        config_['max_func_call_rounds'] = 15
    config_['openai_api_key'] = config_.get('openai_api_key', '')
    config_['openai_model'] = config_.get('openai_model', "gpt-5")
    return config_


class Config(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config_path = "raw/config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        try:
            with open(config_path, "r") as f:
                config_ = json.load(f)
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass
        self.config_path = config_path
        config_ = validate(config_)
        self.update(config_)

    def save(self):
        with open(self.config_path, "w") as g:
            json.dump(self, g, indent=4)
