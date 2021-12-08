# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Prostream By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "File is no longer available" in data:
        return False, "[Prostream] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    ext = 'mp4'

    packed = scrapertools.find_single_match(data, "text/javascript'>(eval.*?)\s*</script>")
    unpacked = jsunpack.unpack(packed)
    media_url = scrapertools.find_single_match(unpacked, r'sources:\s*\["([^"]+)"')
    
    ext = media_url[-4:]
    video_urls.append(["%s [Prostream]" % (ext), media_url])

    return video_urls
