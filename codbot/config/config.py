import configparser
import os

default_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")

class Config:
    def __init__(self):
        self.config = configparser.RawConfigParser()
        self.read_config()

    def read_config(self):
        if os.path.isfile(default_config):
            self.config.read(default_config)
            return

        self.create_config()

    def create_config(self):
        self.config.set('DISCORD', 'token', '')

        with open(default_config, 'w') as f:
            self.config.write(f)

    @property
    def discord_token(self):
        return self.config.get('DISCORD', 'token')