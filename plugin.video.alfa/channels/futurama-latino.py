# -*- coding: utf-8 -*-
# -*- Channel Futurama-latino -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import base64

from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay


IDIOMAS = {'latino': 'LAT'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['fembed', 'vidcloud']

host = "https://futurama-latino.net/"


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    return seasons(item)


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def seasons(item):
    logger.info()

    itemlist = list()

    if not item.videolibrary:
        autoplay.show_option(item.channel, itemlist)

    soup = create_soup(host)
    matches = soup.find("div", class_="row")

    for elem in matches.find_all("a"):
        url = elem["href"]
        season = scrapertools.find_single_match(url, r"/temporada/(\d+)")
        title = 'Temporada %s' % season
        if 'temporada' in url.lower():
            itemlist.append(Item(channel=item.channel, title=title, action="episodesxseason", url=url,
                                 contentSerieName='Futurama', infoLabels={"season": season}))
        elif not item.videolibrary:
            contentTitle = scrapertools.find_single_match(url, 'net/futurama-([^/]+)').replace('-', ' ')
            itemlist.append(Item(channel=item.channel, title=title, action="findvideos", url=url,
                                 contentTitle=contentTitle, infoLabels={'year': '-'}))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName='Futurama',
                 extra1='library'))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    item.videolibrary = True
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    matches = soup.find_all("div", class_="item")
    infoLabels = item.infoLabels
    for elem in matches:
        url = elem.a["href"]
        title = elem.find("div", class_="data-sort-title").text.replace(u"\xd7", "x")
        episode = title.split(":")[0].split("x")[1]
        infoLabels["episode"] = episode
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    player_data = soup.find("div", class_="item get_player_content")["data-player-content"]
    player = scrapertools.find_single_match(player_data, 'iframe src="([^"]+)"')

    soup = create_soup(player, referer=item.url)

    matches = soup.find_all("div", class_="btn-embed")

    for elem in matches:
        url = base64.b64decode(elem["data-embed"]+'==')
        itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', language='LAT'))

    servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server)

    return itemlist
