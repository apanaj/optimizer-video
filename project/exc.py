class AppException(Exception):
    pass


class LargeFileException(AppException):
    message = 'File is too large'
    status = 413


class FileSizeException(AppException):
    message = 'File not found or file length is zero'
    status = 400


class FileNotFoundException(AppException):
    message = 'File not found'
    status = 404


class FileNotValidException(AppException):
    message = 'File is not valid'
    status = 400


class FileNotDownloadException(AppException):
    message = 'File not downloaded'
    status = 400


class WebhookRequiredException(AppException):
    message = '`webhook` parameter required'
    status = 400


class WebhookNotValidException(AppException):
    message = '`webhook` is not valid'
    status = 403


class WatermarkIsNotValidException(AppException):
    message = '`Watermark` is not valid'
    status = 400


class ServerHostIsNotValidException(AppException):
    message = '`SERVER_HOST` is not valid'
    status = 400
