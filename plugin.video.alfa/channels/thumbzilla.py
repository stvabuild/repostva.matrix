# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from core import channeltools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

canonical = {
             'channel': 'thumbzilla', 
             'host': config.get_setting("current_host", 'thumbzilla', default=''), 
             'host_alt': ["https://thumbzilla.com"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="videos", title="Más Calientes", url=host,
                         viewmode="movie", thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=item.channel, title="Nuevas", url=host + '/newest',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=item.channel, title="Tendencias", url=host + '/trending',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=item.channel, title="Mejores Videos", url=host + '/top',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=item.channel, title="Populares", url=host + '/popular',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=item.channel, title="Videos en HD", url=host + '/hd',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=item.channel, title="Caseros", url=host + '/hd',
                         action="videos", viewmode="movie_with_plot", viewcontent='homemade',
                         thumbnail=get_thumb("channels_adult.png")))
 
    itemlist.append(Item(channel=item.channel, title="PornStar", action="catalogo",
                         url=host + '/pornstars/', viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))
 
    itemlist.append(Item(channel=item.channel, title="Categorías", action="categorias",
                         url=host, viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    # itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host,
                         # thumbnail=get_thumb("channels_adult.png"), extra="buscar"))
    return itemlist


# REALMENTE PASA LA DIRECCION DE BUSQUEDA

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "video/search?q={0}".format(texto))
    # item.url = item.url % tecleado
    item.extra = "buscar"
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def videos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a class="[^"]+" href="([^"]+)">'  # url
    patron += '<img id="[^"]+".*?src="([^"]+)".*?'  # img
    patron += '<span class="title">([^<]+)</span>.*?'  # title
    patron += '<span class="duration"(.*?)</a>'  # time
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedtime in matches:
        time = scrapertools.find_single_match(scrapedtime, '>([^<]+)</span>')
        title = "[%s] %s" % (time, scrapedtitle)
        if ">HD<" in scrapedtime:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time, scrapedtitle)
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, thumbnail=scrapedthumbnail,
                             url=host + scrapedurl, contentTitle=title, fanart=scrapedthumbnail))
    paginacion = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />').replace('amp;', '')
    if paginacion:
        itemlist.append(Item(channel=item.channel, action="videos", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=paginacion))
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<li class="pornstars">.*?<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(Item(channel=item.channel, action="videos", url=url, title=scrapedtitle, fanart=scrapedthumbnail,
                             thumbnail=scrapedthumbnail, viewmode="movie_with_plot"))
    paginacion = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />').replace('amp;', '')
    if paginacion:
        itemlist.append(Item(channel=item.channel, action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=paginacion))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.find_single_match(data, '<p>Categories</p>(.*?)</nav>')
    patron = '<a href="([^"]+)".*?'  # url
    patron += '<span class="wrapper">([^<]+)<span class="count">([^<]+)</span>'  # title, vids
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl,title, vids in matches:
        title = "%s (%s)" % (title, vids)
        thumbnail = item.thumbnail
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(Item(channel=item.channel, action="videos", title=title, url=url, contentTile = title, 
                                  fanart=thumbnail, thumbnail=thumbnail, viewmode="movie_with_plot"))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    url = scrapertools.find_single_match(data,'"link_url":"([^"]+)"')
    url = url.replace("\\", "")
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    url = scrapertools.find_single_match(data,'"link_url":"([^"]+)"')
    url = url.replace("\\", "")
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist