# -*- coding: utf-8 -*-
# -*- Channel Ver-Peliculasrd -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import re

from core import httptools
from core import servertools
from core import scrapertools
from core import tmdb
from core.item import Item
from channelselector import get_thumb
from platformcode import config, logger
from bs4 import BeautifulSoup

IDIOMAS = {}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = []

host = "http://ver-peliculasrd.com/"


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(
        Item(
            action="list_all",
            channel=item.channel,
            thumbnail=get_thumb("movies", auto=True),
            title="Peliculas",
            url=host,
            viewType="movies"
        )
    )

    itemlist.append(
        Item(
            action="genres",
            channel=item.channel,
            thumbnail=get_thumb("genres", auto=True),
            title="Géneros",
            url=host,
            viewType="videos"
        )
    )

    itemlist.append(
        Item(
            action="years",
            channel=item.channel,
            thumbnail=get_thumb("year", auto=True),
            title="Años",
            url=host,
            viewType="videos"
        )
    )

    itemlist.append(
        Item(
            action="search",
            channel=item.channel,
            thumbnail=get_thumb("search", auto=True),
            title="Buscar...",
            url=host,
            viewType="videos"
        )
    )

    return itemlist


def get_source(url, soup=False, json=False, unescape=False, **opt):
    logger.info()

    data = httptools.downloadpage(url, soup=soup, encoding="utf-8", **opt)

    if json:
        data = data.json
    elif soup:
        data = data.soup
    else:
        data = scrapertools.unescape(data.data) if unescape else data.data

    return data


def genres(item):
    logger.info()

    itemlist = []
    soup = get_source(item.url, soup=True)
    matches = soup.find(class_="item-genres").find_all("li")

    for elem in matches:
        elem = elem.find("a")
        gencount = int(elem.find("span").text)

        if gencount < 1: continue

        title = "{} ({})".format(str(elem.contents[2]).strip(), gencount)
        url = "{}{}".format(host, elem["href"])

        itemlist.append(
            Item(
                action="list_all",
                channel=item.channel,
                title=title,
                url=url,
                viewType="movies"
            )
        )

    return itemlist


def years(item):
    logger.info()

    itemlist = []
    soup = get_source(item.url, soup=True)
    matches = soup.find(class_="years").find("ul").find_all("li")

    for elem in matches:
        elem = elem.find("a")

        if elem["href"] == "#": continue

        title = "{}".format(elem.text.strip())
        url = "{}{}".format(host, elem["href"])

        itemlist.append(
            Item(
                action="list_all",
                channel=item.channel,
                title=title,
                url=url,
                viewType="movies"
            )
        )

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = get_source(item.url, soup=True)
    matches = soup.find(class_="main-temporadas").find(class_="items-temporadas").find_all(class_="item-temporada")
    pagination = False

    if len(matches) > 30:
        pagination = True
        start = item.page if isinstance(item.page, int) else 0
        end = start + 30
        matches = matches[start:end]

    for elem in matches:
        thumb_elem = elem.find(class_="item-picture")
        thumb = "{}{}".format(host, thumb_elem.find("img")["data-src"].strip())
        title = elem.find(class_="item-detail").text.strip()
        year = thumb_elem.find(class_="year").text.strip()
        url = "{}{}".format(host, elem.find("a")['href'].strip())

        itemlist.append(
            Item(
                action="findvideos",
                channel=item.channel,
                contentTitle=title,
                infoLabels={"year": year},
                thumbnail=thumb,
                title=title,
                url=url
            )
        )

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginacion

    if pagination:
        itemlist.append(
            Item(
                action="list_all",
                channel=item.channel,
                page=end,
                title='Siguiente >>',
                url=item.url,
            )
        )

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = BeautifulSoup(get_source(item.url), "html5lib")
    urls_list = soup.find(class_="player_download").find(class_="level2").find_all(class_="tab-video")
    # duration = metadata.find("ion-icon", {"name": "hourglass"}).parent.find(class_="text-descripcion").text
    # duration = scrapertools.find_single_match(duration, "(\d+):(\d+):(\d+)")
    # item.infoLabels["duration"] = (((int(duration[0]) * 60) * 60) + (int(duration[1]) * 60))

    if not item.infoLabels["plot"]:
        metadata = soup.find(class_="serie-info")
        item.infoLabels["plot"] = metadata.find(class_="text-descripcion sinopsis").text

    for elem in urls_list:
        url = elem["data-source"]
        if not url: continue

        quality = elem["data-quality"]

        itemlist.append(
            Item(
                action="play",
                channel=item.channel,
                infoLabels=item.infoLabels,
                quality=quality,
                title="%s [%s]",
                url=url,
                infolabels=item.infoLabels
            )
        )

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % (i.server, i.quality))

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(
                action="add_pelicula_to_library",
                channel=item.channel,
                contentTitle=item.contentTitle,
                extra="findvideos",
                text_color="yellow",
                title='Añadir esta pelicula a la videoteca',
                url=item.url
            )
        )

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
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas', 'terror', 'torrent']:
            item.url = host
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
