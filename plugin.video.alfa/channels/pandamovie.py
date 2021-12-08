# -*- coding: utf-8 -*-
# ------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from platformcode import config, logger
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools
from channels import filtertools
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = ['mangovideo']


host = 'https://pandamovies.pw'    #  https://pandamovies.pw  'https://watchpornfree.info'   'https://xxxparodyhd.net'  
                                   #  https://www.netflixporno.net  https://xxxscenes.net  playpornx

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []
    itemlist.append(item.clone(title="Peliculas", action="lista", url=host + "/movies"))
    itemlist.append(item.clone(title="Canal", action="categorias", url=host + "/movies"))
    itemlist.append(item.clone(title="Categorias", action="categorias", url=host + "/movies"))
    itemlist.append(item.clone(title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Categorias":
        data = scrapertools.find_single_match(data, '<a href="#">Genres</a>(.*?)</ul>')
    else:
        data = scrapertools.find_single_match(data, '<a href="#">Studios</a>(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        if not scrapedurl.startswith("https"):
            scrapedurl = "https:%s" % scrapedurl
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div data-movie-id="\d+".*?'
    patron += '<a href="([^"]+)".*?oldtitle="([^"]+)".*?'
    patron += '<img data-original="([^"]+)".*?'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail,
                             fanart=thumbnail, plot=plot, contentTitle=title))
    next_page = scrapertools.find_single_match(data, '<li class=\'active\'>.*?href=\'([^\']+)\'>')
    if next_page == "":
        next_page = scrapertools.find_single_match(data, '<a.*?href="([^"]+)" >Next &raquo;</a>')
    if next_page != "":
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    video_urls = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    links_data = scrapertools.find_single_match(data, '<div id="pettabs">(.*?)<div id="pettabs">')
    patron = 'href="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(links_data)
    for url in matches:
        if not url in video_urls:
            video_urls += url
            itemlist.append(item.clone(title='%s', url=url, action='play', language='VO',contentTitle = item.contentTitle))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist
