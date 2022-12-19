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

canonical = {
             'channel': 'porn300', 
             'host': config.get_setting("current_host", 'porn300', default=''), 
             'host_alt': ["https://www.porn300.com"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevas" , action="lista", url=host + "/en_US/ajax/page/list_videos/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/channels/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="categorias", url=host + "/pornstars/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/?q=%s&page=1" % (host, texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if "categories" in item.url:
        patron  = '<li class="grid__item grid__item--category">.*?'
        patron += '<a href="([^"]+)".*?'
        patron += 'data-src="([^"]+)" alt=.*?'
        patron += '<h3 class="grid__item__title grid__item__title--category">([^<]+)</h3>.*?'
        patron += '</svg>([^<]+)<'
    else:
        patron  = '<a itemprop="url" href="/([^"]+)".*?'
        patron += 'data-src="([^"]+)" alt=.*?'
        patron += 'itemprop="name">([^<]+)</h3>.*?'
        patron += '</svg>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        cantidad = re.compile("\s+", re.DOTALL).sub(" ", cantidad)
        title = "%s (%s)" %(scrapedtitle,cantidad)
        if not "categories" in item.url:
            scrapedurl = scrapedurl.replace("channel/", "producer/")
            scrapedurl = "/en_US/ajax/page/show_%s?page=1" %scrapedurl
        else:
            scrapedurl = "%s%s?page=1" %( host,scrapedurl)
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)" />')
    if next_page=="":
        if "/?page=1" in item.url:
            next_page=urlparse.urljoin(item.url,"/?page=2")
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)" data-video-id=.*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '<span class="duration-video">([^<]+)<.*?'
    patron += '<h3 [^>]+>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtime,scrapedtitle  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        scrapedtime = scrapedtime.strip()
        title = "[COLOR yellow]%s[/COLOR] %s" % (scrapedtime,scrapedtitle)
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title , url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle) )
    prev_page = scrapertools.find_single_match(item.url,"(.*?)page=\d+")
    num= int(scrapertools.find_single_match(item.url,".*?page=(\d+)"))
    num += 1
    num_page = "?page=%s" %num
    if num_page!="":
        next_page = urlparse.urljoin(item.url,num_page)
        if "search" in next_page:
            next_page = prev_page + num_page
            next_page = next_page.replace("&?", "&")
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<source src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url  in matches:
        url = url.replace("amp;", "")
        itemlist.append(Item(channel=item.channel, action="play", title="Directo", url=url, contentTitle=item.contentTitle))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<source src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url  in matches:
        url = url.replace("amp;", "")
        itemlist.append(Item(channel=item.channel, action="play", url=url, contentTitle=item.contentTitle))
    return itemlist