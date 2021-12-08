# -*- coding: utf-8 -*-
# -*- Channel SleazeMovies -*-
# -*- Created for Alfa-addon -*-
# -*- By Sculkurt -*-

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

host = 'http://www.eroti.ga/'   #'http://www.eroti.ga/'  'https://www.sleazemovies.com/'


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(item.clone(title="Todas", action="list_all", url=host, thumbnail=get_thumb('all', auto=True)))
    itemlist.append(item.clone(title="Generos", action="genero", url=host, thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(item.clone(title="Buscar", action="search", thumbnail=get_thumb('search', auto=True)))

    return itemlist


def search(item, texto):
    logger.info()
    if texto != "":
        texto = texto.replace(" ", "+")
    item.url = "%s?s=%s" % (host, texto)
    item.extra = "busqueda"
    try:
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def genero(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li class="cat-item.*?<a href="([^"]+)".*?>([^<]+)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action='list_all', title=scrapedtitle, url=scrapedurl))
    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)  # Eliminamos tabuladores, dobles espacios saltos de linea, etc...
    patron = '<articleid="post-\d+".*?'
    patron += 'h2 class="entry-title"><a href="([^"]+)".*?>([^<]+).*?'
    patron += '<div class="twp-article-post-thumbnail">.*?'
    patron += 'src="([^?]+).*?'
    patron += '<p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, img, plot in matches:
        scrapedtitle = scrapedtitle.replace("&#8217;", "'")
        contentTitle = scrapertools.find_single_match(scrapedtitle, '([^\(]+)')
        year = scrapertools.find_single_match(scrapedtitle, '(\d{4})')
        if not year:
            year = scrapertools.find_single_match(scrapedtitle, '\((\d{4})\)')
        title = "%s %s" %(contentTitle, year)
        if not year:
            year = "-"
        itemlist.append(item.clone(action = "findvideos", title = title, contentTitle = contentTitle, url = scrapedurl,
                             thumbnail = img, plot=plot, contentType = "movie", infoLabels = {'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)

    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)"')
    if next_page != "":
	    itemlist.append(item.clone(action="list_all", title=">> Página siguiente", url=next_page, folder=True))
    return itemlist


def findvideos(item): 
    logger.info() 
    itemlist = [] 
    data = httptools.downloadpage(item.url).data 
    id = scrapertools.find_single_match(data, 'src=".*?vid=([^"]+)"').replace("amp;", "")
    post = "vid=%s&alternative=sleazyvids&ord=0" % id
    url = "https://www.eroti.ga/player/ajax_sources.php"
    data = httptools.downloadpage(url, post=post).data
    url = scrapertools.find_single_match(data, '"file":"([^"]+)"').replace("\/", "/").replace(" ", "%20")
    url += "|Referer=%s" % item.url
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(item.clone(title = '[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url = item.url,
                             action = "add_pelicula_to_library",
                             extra = "findvideos",
                             contentTitle = item.contentTitle,
                             thumbnail = item.thumbnail))
    return itemlist 

