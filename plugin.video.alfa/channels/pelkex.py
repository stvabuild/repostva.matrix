# -*- coding: utf-8 -*-
# -*- Channel Pelkex -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools
from bs4 import BeautifulSoup
from lib import generictools

host = 'http://newpelis.nl/'

list_language = ["LAT"]
list_quality = list()
list_servers = ['zplayer', 'streamtape', 'mega', 'torrent']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host,
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Mas Vistas", action="list_all", url=host + "favorites",
                         thumbnail=get_thumb('more watched', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Años", action="section", thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


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


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="cf")
    for elem in matches.find_all("article", class_=re.compile("shortstory cf")):
        url = elem.a["href"]
        title = elem.a.text.strip()
        thumb = elem.find("img")["src"]
        extra_info = elem.find_all("span", class_="kinopoisk")
        lang = extra_info[0].text
        try:
            year = extra_info[1].text
        except:
            year = "-"

        itemlist.append(Item(channel=item.channel, title=title, contentTitle=title, url=url, action="findvideos",
                            thumbnail=thumb, language=lang, infoLabels={'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find_all("a", class_="page-numbers")[-1]["href"]

        if url_next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all',
                                 section=item.section))
    except:
        pass

    return itemlist


def section(item):
    logger.info()
    itemlist = list()

    soup = create_soup(host)

    action = 'list_all'
    menu = soup.find_all("ul", id="menu-home")
    if item.title == "Generos":
        matches = menu[0].find_all("li", class_="menu-item")
    else:
        matches = menu[1].find_all("li", class_="menu-item")

    for elem in matches:
        url = elem.a["href"]
        if not url.startswith("http"):
            url = host + url
        title = elem.a.text
        itemlist.append(Item(channel=item.channel, title=title, url=url, action=action, section=item.section))

    if item.title == "Generos":
        return itemlist
    else:
        return itemlist[::-1]


def findvideos(item):
    logger.info()

    itemlist = list()
    content_id = scrapertools.find_single_match(item.url, "/(\d+)")

    soup = create_soup(item.url)
    try:
        enc_url = soup.find("a", href=re.compile("http://acortaenlace"))["href"]
        url = generictools.convert_url_base64(enc_url)
        itemlist.append(Item(channel=item.channel, title="Torrent", url=url, server="torrent", action="play",
                             language="LAT", infoLabels=item.infoLabels))
    except:
        pass

    strm_url = "%swp-json/elifilms/movies/?id=%s" % (host, content_id)

    json_data = httptools.downloadpage(strm_url).json
    for v_data in json_data["data"]["server_list"]:
        url = v_data["link"]
        server = v_data["name"].lower()

        itemlist.append(Item(channel=item.channel, title=server.capitalize(), url=url, action="play",
                             language="LAT", infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist)

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
        if categoria in ['peliculas', 'latino', 'torrent']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + 'category/infantil'
        elif categoria == 'terror':
            item.url = host + 'category/terror'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist




