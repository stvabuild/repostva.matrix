# -*- coding: utf-8 -*-
# -*- Channel Pelisplus -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
from lib import generictools
from bs4 import BeautifulSoup

list_language = ['LAT']

list_quality = []

list_servers = [
    'directo',
    'vidlox',
    'fembed',
    'uqload',
    'gounlimited',
    'fastplay',
    'mixdrop',
    'mystream'
    ]

host = 'https://pelisplushd.net/'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Peliculas", action="sub_menu",
                         thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Series", action="sub_menu",
                         thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Anime", action="sub_menu",
                         thumbnail=get_thumb('anime', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Doramas", action="list_all", url=host + "generos/dorama",
                         content="serie", thumbnail=get_thumb('doramas', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + 'search/?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()
    itemlist = list()

    if item.title.lower() == "anime":
        content = item.title.lower()
        item.title = "Animes"
    else:
        content = item.title.lower()[:-1]

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host + '%s' % item.title.lower(),
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Mas Vistas", action="list_all",
                         url=host + '%s/populares' % item.title.lower(),
                         thumbnail=get_thumb('more watched', auto=True), type=content))

    if item.title.lower() == "peliculas":
        itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                             thumbnail=get_thumb('genres', auto=True), type=content))
    elif item.title.lower() == "series":
        itemlist.append(Item(channel=item.channel, title="Mas Vistas", action="list_all",
                             url=host + 'series/populares', thumbnail=get_thumb('more watched', auto=True), type=content))
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

    matches = soup.find("div", class_="Posters")

    for elem in matches.find_all("a"):
        url = elem["href"]
        thumb = elem.img["src"]
        title = scrapertools.find_single_match(elem.p.text, r"(.*?) \(")
        year = scrapertools.find_single_match(elem.p.text, r"(\d{4})")

        if item.type and item.type.lower() not in url:
            continue
        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})

        if "/pelicula/" in url:
            new_item.contentTitle = title
            new_item.action = "findvideos"
        else:
            new_item.contentSerieName = title
            new_item.action = "seasons"

        itemlist.append(new_item)
    tmdb.set_infoLabels_itemlist(itemlist, True)
    #  Paginación

    try:
        next_page = soup.find("a", class_="page-link", rel="next")["href"]

        if next_page:
            if not next_page.startswith(host):
                next_page = host + next_page
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()
    soup = create_soup(item.url).find("ul", class_="TbVideoNv nav nav-tabs")
    matches = soup.find_all("li")
    infoLabels = item.infoLabels

    for elem in matches:
        title = " ".join(elem.a.text.split()).capitalize()
        infoLabels["season"] = scrapertools.find_single_match(title, "Temporada (\d+)")
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

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
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    try:
        matches = create_soup(item.url).find("div", id="pills-vertical-%s" % season).find_all("a")
    except:
        matches = ""

    if not matches:
        return itemlist

    for elem in matches:
        url = elem["href"]
        epi_num = scrapertools.find_single_match(elem.text, "E(\d+)")
        epi_name = scrapertools.find_single_match(elem.text, ":([^$]+)")
        infoLabels['episode'] = epi_num
        title = '%sx%s - %s' % (season, epi_num, epi_name.strip())

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def section(item):
    logger.info()
    itemlist = list()

    soup = create_soup(host).find("aside", class_="side-nav expand-lg")
    matches = soup.find_all("ul", class_="dropdown-menu")[3]
    for elem in matches.find_all("li"):
        title = elem.a.text
        #url = '%s/%s' % (host, elem.a["href"])
        url = urlparse.urljoin(host, elem.a["href"])
        itemlist.append(Item(channel=item.channel, url=url, title=title, action='list_all', type=item.type))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()


    data = httptools.downloadpage(item.url, forced_proxy_opt='ProxyCF')

    if data.sucess or data.code == 302:
        data = data.data

    pattern = "video\[\d+\]\s*=\s*'([^']+)'"
    matches = re.compile(pattern, re.DOTALL).findall(data)

    for url in matches:
        if "https://pelisplushd.me" in url:
            url = url.replace("pelisplushd.me", "feurl.com")
        if "https://pelisplushd.net/fembed.php" in url:
            url= url.replace("pelisplushd.net/fembed.php?url=", "https://feurl.com/v/")
        itemlist.append(Item(channel=item.channel, title='%s [%s]', url=url, action='play', language="LAT",
        infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % (i.server.capitalize(), i.language))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_pelicula_to_library",
                                 extra="findvideos",
                                 contentTitle=item.contentTitle))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url += texto

    try:
        if texto != '':
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas', 'latino']:
            item.url = host + 'peliculas/estrenos'
        elif categoria == 'infantiles':
            item.url = host + 'generos/animacion/'
        elif categoria == 'terror':
            item.url = host + 'generos/terror/'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist