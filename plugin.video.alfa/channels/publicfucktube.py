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
from bs4 import BeautifulSoup
# from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = []

host = 'https://publicfucktube.com'   #yeapornplease 'https://pornwild.to' # 'https://0dayporn.com'


def mainlist(item):
    logger.info()
    itemlist = []

    # autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?filter=latest"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/?filter=most-viewed"))
    itemlist.append(item.clone(title="Mas metraje" , action="lista", url=host + "/?filter=longest"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))

    # autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/%s/" % (host,texto)
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
    soup = create_soup(item.url)
    matches = soup.find('div', class_='videos-list')
    for elem in matches.find_all('article'):
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('a', class_='current').parent
    if next_page.find_next_sibling("li"):
        next_page = next_page.find_next_sibling("li").a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    if "/search/" in item.url:
        matches = soup.find('section', id='primary')
    else:
        matches = soup.find('div', class_='videos-list')
    for elem in matches.find_all('article'):
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['data-src']
        time = elem.find('span', class_='duration')
        quality = elem.find('span', class_='hd-video')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time.text,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time.text,title)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='current').parent
    if next_page.find_next_sibling("li"):
        next_page = next_page.find_next_sibling("li").a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='responsive-player')
    url = soup.iframe['src']
    if "player-x.php" in url:
        import base64
        decode = scrapertools.find_single_match(url,'.*?php\?q=([A-z0-9=]+)')
        decode = base64.b64decode(decode).decode("utf8")
        decode = urlparse.unquote(decode)
        url = scrapertools.find_single_match(decode,'src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='responsive-player')
    url = soup.iframe['src']
    if "player-x.php" in url:
        import base64
        decode = scrapertools.find_single_match(url,'.*?php\?q=([A-z0-9=]+)')
        decode = base64.b64decode(decode).decode("utf8")
        decode = urlparse.unquote(decode)
        url = scrapertools.find_single_match(decode,'src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist