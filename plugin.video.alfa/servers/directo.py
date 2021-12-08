# -*- coding: utf-8 -*-

from platformcode import logger
from core import scrapertools


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    invaid_url ="No se ha encontrado un enlace. " \
                "Posiblemente sea un servidor no soportado."

    exists = True if page_url else False
    reason = invaid_url if not exists else ""
    page_url, ignore_response_code = page_url.split("|")[0], True if "|ignore_response_code=True" in page_url else page_url, False

    if page_url:
        pattern = r'(?:^[A-Za-z]+://|^/|^[A-Za-z]+:[\\/]+)\S+'
        match = scrapertools.find_single_match(page_url, pattern)
        exists = True if match else False
        reason = "" if exists else "Ruta o enlace inválido."

        if page_url.startswith('http'):
            from core import httptools
            response = httptools.downloadpage(page_url, only_headers=True, ignore_response_code=ignore_response_code)

            if not ignore_response_code and not response.sucess:
                exists = False
                reason = "El archivo no existe." if response.code == 404 else "Se ha producido un error en el servidor (%s)" % response.code

            else:
                content_type = response.headers.get('Content-Type', '').split(";")[0]
                exists = False if 'text' in content_type else True
                reason = "El enlace no es un video (se encontró tipo %s)." % content_type if not exists else ""

    if not exists and not ignore_response_code:
        reason += " Repórtalo en el foro https://alfa-addon.com\n"
    else:
        reason = "Ha ocurrido un error con este video"

    return exists, reason

# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    video_urls = [["%s [directo]" % page_url[-4:], page_url]]

    return video_urls
