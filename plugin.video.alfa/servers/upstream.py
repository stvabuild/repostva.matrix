# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Upstream By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack

page = ''

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    global page
    page = httptools.downloadpage(page_url)

    if page.code == 404 or '"title">File Not Found</div>' in page.data \
    or 'player_blank.jpg' in page.data or 'assets/images/image-404.png' in page.data:
        return False, "[upstream] El archivo no existe o  ha sido borrado"

    elif '_msg">File was locked by administrator</div>' in page.data:
        return False, "[upstream] Archivo bloqueado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    data = page.data
    video_urls = []
    packed = scrapertools.find_single_match(data, "text/javascript'>(eval.*?)\s*</script>")

    if packed:
        data = jsunpack.unpack(packed)

    patron = 'file:"([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url in matches:
        ext = url[-4:]
        if ext == '.srt' or ext == '.jpg':
            continue
        url += '|Referer=%s' % page_url
        video_urls.append(["%s [Upstream]" % ext, url])

    return video_urls
