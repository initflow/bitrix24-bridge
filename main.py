import uvicorn
from bitrix24 import Bitrix24

from bridge.app import create_app


def main():
    bx24 = Bitrix24(
        domain='b24-me95d6.bitrix24.ru',
        client_id='local.5d1dcd73f37b93.64520037',
        client_secret='KMeHJ8jlOSkvFS43zUsbs2jg1p0sGgIR9F4pk3X9Vt9hZEj21L'
    )
    print(bx24.resolve_authorize_endpoint())
    print(bx24.request_tokens('requested_authorization_code'))
    print(bx24.get_tokens())


if __name__ == '__main__':
    # main()
    uvicorn.run(create_app(), host='0.0.0.0', port=8000, log_level='debug')