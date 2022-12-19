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
from bs4 import BeautifulSoup
from channels import filtertools
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['vidlox']

# vidlox y netu al primero le cuesta cargar


canonical = {
             'channel': 'xxxfreeinhd', 
             'host': config.get_setting("current_host", 'xxxfreeinhd', default=''), 
             'host_alt': ["https://xxxfree.watch"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/page/1/?filter=latest"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/page/1/?filter=most-viewed"))
    itemlist.append(item.clone(title="Mas popular" , action="lista", url=host + "/page/1/?filter=popular"))
    itemlist.append(item.clone(title="Mas largo" , action="lista", url=host + "/page/1/?filter=longest"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
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
    soup = create_soup(item.url)
    matches = soup.find_all('article', class_=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img
        if thumbnail:
            thumbnail = thumbnail['src']
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot, fanart=thumbnail) )
    next_page = soup.find('a', class_='current')
    if next_page and next_page.parent.find_next_sibling("li"):
        next_page = next_page.parent.find_next_sibling("li").a['href']
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
    matches = soup.find_all('article', class_=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['data-src']
        time = elem.find('div', class_='card-movie-duration')
        if time:
            time = time.text.strip()
            title = "[COLOR yellow]%s[/COLOR] %s" % (time, title)
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, contentTitle = title, url=url,
                              thumbnail=thumbnail, plot=plot, fanart=thumbnail ))
    next_page = soup.find('a', class_='current')
    if next_page and next_page.parent.find_next_sibling("li"):
        next_page = next_page.parent.find_next_sibling("li").a['href']
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', class_='responsive-player').find_all('iframe')
    for elem in matches:
        url = elem['src']
        itemlist.append(item.clone(action="play", title = "%s", contentTitle= item.title, url=url ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist


def decode_url(txt):
    import base64
    logger.info()
    itemlist = []
    data = httptools.downloadpage(txt).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    n = 2
    while n > 0:
        b64_url = scrapertools.find_single_match(data, '\(dhYas638H\("([^"]+)"\)')
        b64_url = base64.b64decode(b64_url + "=")
        b64_url = base64.b64decode(b64_url + "==")
        data = b64_url.decode("utf8")
        n -= 1
    url = scrapertools.find_single_match(b64_url, '<iframe src="([^"]+)"')
    url = httptools.downloadpage(url).url
    return url

