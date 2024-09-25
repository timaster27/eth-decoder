import traceback

from settings import ADMIN_IDS


def alive(client):
    client.send_message(ADMIN_IDS[0], 'bot is alive')


def send_error(client):
    def decorate(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except:
                traceback.print_exc()
                client.send_message(ADMIN_IDS[0], traceback.format_exc())

        return wrapper

    return decorate
