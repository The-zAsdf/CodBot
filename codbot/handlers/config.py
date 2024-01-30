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
        self.config.set('COD', 'token', '')
        self.config.set('RCON', 'token', '')
        self.config.set('GOOGL', 'token', '')

        with open(DEFAULT_CONFIG, 'w+') as f:
            self.config.write(f)

    @property
    def discord_token(self):
        return self.config.get('DISCORD', 'token')
    
    @property
    def cod_token(self):
        return self.config.get('COD', 'token')
    
    @property
    def rcon_token(self):
        return self.config.get('RCON', 'token')
    
    @property
    def googl_token(self):
        return self.config.get('GOOGL', 'token')