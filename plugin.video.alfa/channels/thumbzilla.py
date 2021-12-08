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

__channel__ = "thumbzilla"


host = 'https://thumbzilla.com'
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFF6E2802', '0xFFFAA171', '0xFFE9D7940'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E64FE', '0xFF0404B4']]

if __perfil__ - 1 >= 0:
    color1, color2, color3 = perfil[__perfil__ - 1]
else:
    color1 = color2 = color3 = ""

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
thumbnail = 'https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/adults/%s.png'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="videos", title="Más Calientes", url=host,
                         viewmode="movie", thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(item.clone(title="Nuevas", url=host + '/newest',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(item.clone(title="Tendencias", url=host + '/trending',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(item.clone(title="Mejores Videos", url=host + '/top',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(item.clone(title="Populares", url=host + '/popular',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(item.clone(title="Videos en HD", url=host + '/hd',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(item.clone(title="Caseros", url=host + '/hd',
                         action="videos", viewmode="movie_with_plot", viewcontent='homemade',
                         thumbnail=get_thumb("channels_adult.png")))
 
    itemlist.append(item.clone(title="PornStar", action="catalogo",
                         url=host + '/pornstars/', viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))
 
    itemlist.append(item.clone(title="Categorías", action="categorias",
                         url=host, viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(item.clone(title="Buscar", action="search", url=host,
                         thumbnail=get_thumb("channels_adult.png"), extra="buscar"))
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
        itemlist.append(item.clone(action=action, title=title, thumbnail=scrapedthumbnail,
                             url=host + scrapedurl, contentTitle=title, fanart=scrapedthumbnail))
    paginacion = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />').replace('amp;', '')
    if paginacion:
        itemlist.append(item.clone(action="videos", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=paginacion))
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
        itemlist.append(item.clone(action="videos", url=url, title=scrapedtitle, fanart=scrapedthumbnail,
                             thumbnail=scrapedthumbnail, viewmode="movie_with_plot"))
    paginacion = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />').replace('amp;', '')
    if paginacion:
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=paginacion))
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
        itemlist.append(item.clone(action="videos", title=title, url=url, contentTile = title, 
                                  fanart=thumbnail, thumbnail=thumbnail, viewmode="movie_with_plot"))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = 'data-quality="([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url,quality in matches:
        url = url.replace("\/", "/")
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = 'data-quality="([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url,quality in matches:
        url = url.replace("\/", "/")
        itemlist.append(['.mp4 %s' %quality, url])
    return itemlist