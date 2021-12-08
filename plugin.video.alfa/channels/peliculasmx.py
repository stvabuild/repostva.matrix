# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re

from core import scrapertools
from core import httptools
from core import tmdb
from core.item import Item

from platformcode import logger

host = "http://www.peliculasmx.net"

def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(
        Item(channel=item.channel, title="Últimas añadidas", action="peliculas", url=host))
    itemlist.append(
        Item(channel=item.channel, title="Últimas por género", action="generos", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + '/category/animacion/'
        elif categoria == 'terror':
            item.url = host + '/category/terror/'
        itemlist = peliculas(item)
        if "Pagina" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<li class="cat-item cat-item-.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '>([^<]+).*?'
    patron += '<span>([^<]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)
    logger.debug(matches)
    for match in matches:
        scrapedurl = urlparse.urljoin("", match[0])
        scrapedtitle = match[1].strip() + ' [' + match[2] + ']'

        itemlist.append(Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=scrapedurl, folder=True))

    itemlist = sorted(itemlist, key=lambda Item: Item.title)
    return itemlist


def peliculas(item):
    logger.info()
    extra = item.extra
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    patron = '<div id="mt-.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="tt">([^<]+).*?'
    patron += '<span class="year">(\d{4})</span>.*?'
    patron += '<span class="calidad2">([^<]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year, quality in matches:
        url =scrapedurl
        title = scrapedtitle
        thumbnail = scrapedthumbnail

        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title, contentTitle=title, url=url,
                 thumbnail=thumbnail, quality=quality, infoLabels={'year':year}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, 'class="nextpostslink" rel="next" href="(.*?)">')

    if next_page:
        scrapedtitle = "!Pagina Siguiente ->"
        itemlist.append(Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=next_page, folder=True))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []

    texto = texto.replace(" ", "+")
    try:
        # Series
        item.url = host + "/?s=%s" % texto
        itemlist.extend(peliculas(item))
        itemlist = sorted(itemlist, key=lambda Item: Item.title)

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
