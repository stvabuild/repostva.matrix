# -*- coding: utf-8 -*-
# -*- Channel Locomotion-*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


host = 'http://locomotiontv.com/'


def mainlist(item):
    logger.info()
    itemlist = list()

    data = httptools.downloadpage(host + "envivo").data
    url = scrapertools.find_single_match(data, '<script src="(/dummy/div_vid.js\?[^"]+)"></script>')

    itemlist.append(Item(channel=item.channel, title="Locomotion (Vivo)", url=host + url, action="play", server="directo"))

    return itemlist


def play(item):
    logger.info()

    v_data = httptools.downloadpage(item.url).data
    item.url = scrapertools.find_single_match(v_data, '"src","([^"]+)"')

    return [item]

