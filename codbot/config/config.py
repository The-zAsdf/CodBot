import configparser
import os

DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")

class Config:
    def __init__(self):
        self.config = configparser.RawConfigParser()
        self.read_config()

    def read_config(self):
        if os.path.isfile(DEFAULT_CONFIG):
            self.config.read(DEFAULT_CONFIG)
            return

        self.create_config()

    def create_config(self):
        self.config.add_section('DISCORD')
        self.config.set('DISCORD', 'token', '')

        with open(DEFAULT_CONFIG, 'w+') as f:
            self.config.write(f)

    @property
    def discord_token(self):
        return self.config.get('DISCORD', 'token')