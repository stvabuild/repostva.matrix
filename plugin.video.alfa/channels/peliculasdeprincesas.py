# -*- coding: utf-8 -*-
# -*- Channel Peliculas de Princesas -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from builtins import range
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools
from bs4 import BeautifulSoup

host = 'https://princesas.tv/'

list_language = list()
list_quality = []
list_servers = ['directo']


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


def add_menu_items(item):
    logger.info()

    itemlist = list()

    soup = create_soup(host)
    matches = soup.find_all("li", class_="menu-item")

    for elem in matches[:-1]:
        url = elem.a["href"]
        title = elem.a.text.strip().title()
        
        itemlist.append(Item(channel=item.channel, url=url, title=title, action="get_from_list"))
    return itemlist


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Ultimas", action="list_all", url=host,
                         thumbnail=get_thumb('last', auto=True)))

    itemlist.extend(add_menu_items(item))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + "?s=",
                         thumbnail=get_thumb('search', auto=True), page=1))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url)
    matches = soup.find_all("article", class_="latestPost")

    for elem in matches:
        url = elem.a["href"]
        thumb = elem.img["src"]
        year = scrapertools.find_single_match(elem.a["title"], r"\((\d{4})\)")
        title = re.sub(r" \(%s\)" % year, "", elem.a["title"]).capitalize()
        action = "findvideos"
        if "online" in title.lower() or "películas de" in title.lower():
            title = re.sub(r" \(online\)", "", title.lower()).capitalize()
            action = "get_from_list"

        itemlist.append(Item(channel=item.channel, title=title, url=url, contentTitle=title, action=action,
                             thumbnail=thumb, infoLabels={'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        next_page = soup.find("a", class_="next page-numbers")["href"]

        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist


def get_from_list(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("div", class_="MsoNormal")
    for elem in matches:
        if not elem.find("a"):
            continue
        url = elem.a["href"]
        year = scrapertools.find_single_match(elem.text, "\d{4}")
        title = elem.a.text.capitalize()

        itemlist.append(Item(channel=item.channel, title=title, url=url, contentTitle=title, action="findvideos",
                             infoLabels={'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def genres(item):
    logger.info()
    itemlist = list()

    soup = create_soup(host+'peliculas')

    action = 'list_all'
    matches = soup.find("div", id="panel_genres_filter").find_all("a")
    for elem in matches:

        title = elem.text
        url = "%sresults/?cat=%s&genre=%s&p=" % (host, item.cat, title)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action=action, section=item.section, page=0))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    url = create_soup(item.url).find("iframe")["src"]

    itemlist.append(Item(channel=item.channel, title='%s', url=url, action="play", server="directo",
                         language="LAT", infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                     url=item.url, action="add_pelicula_to_library", extra="findvideos",
                     contentTitle=item.contentTitle))

    return itemlist


def play(item):
    logger.info()

    data = httptools.downloadpage(item.url, headers={"referer": host}).data
    url = scrapertools.find_single_match(data, '"file":"([^"]+)","label":".*?"')
    item = item.clone(url=url + "|referer=%s" % item.url)

    return [item]


def search(item, texto):
    logger.info()

    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto

        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys

        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas', 'infantiles']:
            item.url = host

        item.page=1
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


