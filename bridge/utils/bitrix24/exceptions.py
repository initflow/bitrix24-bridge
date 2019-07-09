class Bitrix24BaseException(Exception):
    pass


class IncorrectTransportType(Bitrix24BaseException):
    pass


class IncorrectCall(Bitrix24BaseException):
    pass
