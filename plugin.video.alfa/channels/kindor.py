# -*- coding: utf-8 -*-
# -*- Channel InkaPelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from core import tmdb
from core import httptools
from core import jsontools
from core.item import Item
from core import scrapertools
from core import servertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
import sys
import base64

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


IDIOMAS = {'0': 'LAT', '1': 'CAST', '2': 'VOSE'}
list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'fembed',
    'streampe',
    'gounlimited',
    'mystream',
    'gvideo'
    ]

host = 'https://kindor.io/'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu',
                         thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'series', action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Novedades', action='list_all', url=host,
                         thumbnail=get_thumb('newest', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Destacadas', action='list_all', url=host + "destacadas",
                         thumbnail=get_thumb('hot', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Recomendadas', action='list_all', url=host + "recomendadas",
                         thumbnail=get_thumb('recomended', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + 'buscar/',
                         thumbnail=get_thumb("search", auto=True)))


    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()
    mode = item.title.lower()

    if item.title == "Peliculas":
        itemlist.append(Item(channel=item.channel, title='Ultimas', url=host + 'peliculas/estrenos', action='list_all',
                             thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + mode, action='list_all',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section', mode=mode,
                         thumbnail=get_thumb('genres', auto=True)))

    # itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
    #                      thumbnail=get_thumb('year', auto=True)))

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)

    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def section(item):
    logger.info()

    itemlist = list()
    base_url = "%s%s" % (host, item.mode)
    soup = create_soup(base_url)

    if item.title == "Generos":
        matches = soup.find("ul", class_="dropm")
    else:
        matches = soup.find("ul", class_="releases scrolling")

    for elem in matches.find_all("li"):
        url = elem.a["href"]
        title = elem.a.text

        itemlist.append(Item(channel=item.channel, title=title, action="list_all", url=url, first=0))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("section", class_="coys").find_all("div", class_="pogd")

    for elem in matches:

        url = elem.h3.a["href"]
        title = elem.h3.text
        try:
            thumb = elem.img["data-src"]
        except:
            thumb = elem.img["src"]
        year = "-"
        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb,
                        infoLabels={"year": year})

        if "serie/" in url:
            new_item.contentSerieName = title
            new_item.action = "seasons"
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find("div", class_="pazza").find("a", class_="ffas").next_sibling["href"]
    except:
        return itemlist

    if url_next_page and len(matches) > 16:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()
    data = httptools.downloadpage(item.url).data
    fom, hash = scrapertools.find_single_match(data, "fom:(.*?),hash:'([^']+)'")
    json_data = jsontools.load(fom)
    infoLabels = item.infoLabels

    for elem in json_data:
        season = elem
        title = "Temporada %s" % season
        infoLabels["season"] = season
        epi_data = json_data[elem]
        itemlist.append(Item(channel=item.channel, title=title, action='episodesxseasons', epi_data=epi_data, hash=hash,
                             context=filtertools.context(item, list_language, list_quality), infoLabels=infoLabels))



    tmdb.set_infoLabels_itemlist(itemlist, True)
    itemlist = sorted(itemlist, key=lambda i: i.contentSeason)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist


def episodesxseasons(item):
    logger.info()

    itemlist = list()
    matches = item.epi_data
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    for epi, info in matches.items():
        title = "%sx%s - %s" % (season, epi, info["name"])
        json_data = info["all"]
        infoLabels["episode"] = epi

        itemlist.append(Item(channel=item.channel, title=title, json_data=json_data, action='findvideos',
                             infoLabels=infoLabels, hash=item.hash))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    itemlist = sorted(itemlist, key=lambda i: i.contentEpisodeNumber)
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    if item.json_data:
        json_data = item.json_data
        hash = item.hash
    else:
        data = httptools.downloadpage(item.url).data
        json_data = jsontools.load(scrapertools.find_single_match(data, "fom:(\{.*?})"))
        hash = scrapertools.find_single_match(data, "hash:'([^']+)'")

    for url_info in json_data:
        lang = url_info
        url = "%s?h=%s" % (base64.b64decode(json_data[url_info]), hash)
        itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url,
                         language=IDIOMAS.get(lang, "VOSE"), infoLabels=item.infoLabels))


    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
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
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'peliculas/estrenos'
        elif categoria == 'infantiles':
            item.url = host + 'peliculas/animacion/'
        elif categoria == 'terror':
            item.url = host + 'peliculas/terror/'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
