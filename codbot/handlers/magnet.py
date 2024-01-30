from pyshorturl import Googl, GooglError
from .config import Config

def shorten(ip:str, port:int):
    link = f'cod4://{ip}:{port}'
    service = Googl(api_key=Config().googl_token)
    try:
        short_url = service.shorten_url(link)
        return short_url
    except GooglError as e:
        print(e)
        return None


