# -*- coding: utf-8 -*-
#------------------------------------------------------------
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
from core.item import Item
from core import servertools
from core import httptools

host = 'https://pornwild.to' # 'https://0dayporn.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/latest-updates/?sort_by=post_date&from=1"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/most-popular/?sort_by=video_viewed_month&from=1"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/top-rated/?sort_by=rating_month&from=1"))
    itemlist.append(item.clone(title="Pornstars" , action="categorias", url=host + "/models/?sort_by=avg_videos_rating&from=1"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/search/%s/?sort_by=post_date" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a class="item".*?'
    patron += 'href="([^"]+)" title="([^"]+)".*?'
    patron += '<div class="img">(.*?)</div>.*?'
    patron += '<div class="videos">([^<]+) videos<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        if "src=" in scrapedthumbnail:
            thumbnail = scrapertools.find_single_match(scrapedthumbnail, 'src="([^"]+)"')
        else:
            thumbnail = ""
        title = "%s (%s)" %(scrapedtitle,cantidad)
        url = urlparse.urljoin(host,scrapedurl)
        itemlist.append(item.clone(action="lista", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail, plot="") )
    if "categories" in item.url:
        itemlist.sort(key=lambda x: x.title)
    next_page = scrapertools.find_single_match(data, '<li class="next">.*?data-parameters="([^"]+)"')
    if next_page:
        next_page = next_page.replace(":", "=").replace(";", "&").replace("+from_albums", "")
        next_page = "?%s" % next_page
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="item  ">.*?'
    patron += '<a href="([^"]+)" title="([^"]+)".*?'
    patron += 'data-original="([^"]+)".*?'
    patron += 'title="(?:Watch Later|Ver más tarde)"(.*?)</div>.*?'
    patron += '<div class="duration">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,quality,time in matches:
        if "HD" in quality:
            quality = "HD"
        else:
            quality =""
        title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time, quality, scrapedtitle)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<li class="next">.*?data-parameters="([^"]+)"')
    if next_page:
        next_page = next_page.replace(":", "=").replace(";", "&").replace("+from_albums", "")
        next_page = "?%s" % next_page
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    data = scrapertools.find_single_match(data, '<div class="player-holder">(.*?)<a href="#like"')
    if "kt_player" in data:
        url = item.url
    else:
        url = scrapertools.find_single_match(data, '<(?:iframe|IFRAME).*?(?:src|SRC)="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    data = scrapertools.find_single_match(data, '<div class="player-holder">(.*?)<a href="#like"')
    if "kt_player" in data:
        url = item.url
    else:
        url = scrapertools.find_single_match(data, '<(?:iframe|IFRAME).*?(?:src|SRC)="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
