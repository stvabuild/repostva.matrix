# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector anonfile By Alfa development Group
# --------------------------------------------------------

from builtins import range
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from core import httptools
from platformcode import logger
from bs4 import BeautifulSoup
from core import jsontools
import base64


def test_video_exists(page_url):
    global data, ref
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url, add_referer=True)
    if not data.sucess:
        return False, "[easyload] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    video_urls = list()
    soup = BeautifulSoup(data.data, "html5lib")
    logger.debug(soup)
    embed_data = soup.find("fileembed-component")["exdata"]
    for x in range(2):
        embed_data = base64.b64decode(embed_data)
    logger.debug(embed_data)
    strm_data = jsontools.load(embed_data)["streams"]

    for strm in strm_data:
        logger.debug(strm)
        src = list(strm_data[strm]["src"])
        t = '15'
        media_url = ''.join(chr(ord(src[n]) ^ ord(t[n % len(t)])) for n in range(len(src)))
        media_url += "|referer=%s" % page_url
        qlty = strm_data[strm]["resolution"]
        video_urls.append(['%sp [easyload]' % qlty, media_url])
    return video_urls
