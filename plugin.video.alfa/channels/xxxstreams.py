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
from core import servertools
from core import httptools
from core.item import Item
from channels import filtertools
from channels import autoplay
from bs4 import BeautifulSoup


IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['gounlimited']

######    k2s
host = 'http://xxxstreams.org' #es http://freepornstreams.org  http://fullxxxmovies.net


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Peliculas" , action="lista", url= host + "/full-adult-movies/new-releases/"))
    itemlist.append(item.clone(title="Videos" , action="lista", url=host + "/new-porn-streaming/"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host))
    # itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
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
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Categorias" :
        data1 = scrapertools.find_single_match(data,'>Top Tags</a>(.*?)</ul>')
        data1 += scrapertools.find_single_match(data,'>Ethnic</a>(.*?)</ul>')
        data1 += scrapertools.find_single_match(data,'>Kinky</a>(.*?)</ul>')
    if item.title == "Canal" :
        data1 = scrapertools.find_single_match(data,'>Top sites</a>(.*?)</ul>')
        data1 += scrapertools.find_single_match(data,'Downloads</h2>(.*?)</ul>')
    patron  = '<a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data1)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append(item.clone(action="findvideos", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
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


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all("article", id=re.compile(r"^post-\d+"))
    logger.debug(matches)
    for elem in matches:
        parte = elem.find('h1', class_='entry-title')
        url = parte.a['href']
        title = parte.text
        if "Siterip" in title or "manyvids" in title:
            title = "[COLOR red]%s[/COLOR]" %title
        thumbnail = elem.img['src']
        if "svg" in thumbnail:
            thumbnail = elem.img['data-lazy-src']
        itemlist.append(item.clone(action="findvideos", title=title, contentTitle=title, url=url,
                               fanart=thumbnail, thumbnail=thumbnail) )
    next_page = soup.find('a', class_='next page-numbers')
    if next_page:
        next_page = next_page['href']
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='entry-content')
    matches = soup.find_all("a")
    for elem in matches:
        url = elem['href']
        if not "imgcloud." in url and not "ubiqfile" in url:
            itemlist.append(item.clone(action="play", title= "%s" , contentTitle=item.title, url=url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist


