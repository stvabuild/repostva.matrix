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
from core.item import Item
from core import httptools
from channels import filtertools
from channels import autoplay
from bs4 import BeautifulSoup


IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = ['gounlimited']

host = 'http://fullxxxmovies.net'          #es   http://freepornstreams.org    http://xxxstreams.org

# k2s

def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Peliculas" , action="lista", url=host + "/streams"))
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.find_single_match(data,'>Main Menu<(.*?)</ul>')
    patron  = '<a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        if not "Featured" in scrapedtitle:
            scrapedplot = ""
            scrapedthumbnail = ""
            scrapedurl = scrapedurl.replace ("http://freepornstreams.org/freepornst/stout.php?s=100,75,65:*&#038;u=" , "")
            itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                                   thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return sorted(itemlist, key=lambda i: i.title)


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
    for elem in matches:
        parte = elem.find('h1', class_='entry-title')
        url = parte.a['href']
        title = parte.a.text
        if "Siterip" in title or "manyvids" in title:
            title = "[COLOR red]%s[/COLOR]" %title
        thumbnail = elem.img['src']
        if "data:image" in thumbnail:
            thumbnail = elem.img['data-lazy-src']
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, url=url, 
                                  thumbnail=thumbnail, fanart=thumbnail, plot=plot) )
    next_page = soup.find('div', class_='nav-previous')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='entry-content')
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        if not "ubiqfile" in url and not "imgcloud" in url:
            itemlist.append(item.clone(action='play',title="%s " + url, contentTitle=item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist
