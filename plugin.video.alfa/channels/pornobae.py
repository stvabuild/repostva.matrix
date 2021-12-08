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
from channels import filtertools
from channels import autoplay
from bs4 import BeautifulSoup


IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['Doodstream']

host = 'https://pornobae.com'


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?filter=latest"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/?filter=most-viewed"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/?filter=popular"))
    itemlist.append(item.clone(title="Mas comentado" , action="lista", url=host + "/?filter=longest"))
    itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "/actors/"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    
    # itemlist.append(item.clone(title="Configurar canal...", text_color="gold", action="configuracion", thumbnail=get_thumb('setting_0.png')))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s&filter=latest" % (host,texto)
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
    matches = soup.find('div', class_='videos-list').find_all('article')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('header').text.strip()
        thumbnail = elem.img['src']
        itemlist.append(item.clone(action="lista", title=title, url=url, fanart =thumbnail, thumbnail=thumbnail) )
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.find_next('a')['href']
        next_page = urlparse.urljoin(host,next_page)
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
    matches = soup.find(id='primary').find_all('article')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('header').text.strip()
        thumbnail = elem.img['data-src']
        time = elem.find('span', class_='duration').text
        title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail,
                                fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.find_next('a')['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    import base64
    soup = create_soup(item.url).find('div', class_='video-description')
    logger.debug(soup)
    matches = soup.find_all('a') #.select('strong') #"Cannot execute CSS selectors because the soupsieve package is not installed."
    for elem in matches:
        title = ""
        url = elem['href'].replace("/go.php?url=", "")
        url = base64.b64decode(url).decode("utf8")
        url = urlparse.unquote(url)
        if not "pixxxels" in url:
            title = elem.text
        if "HD" in title:
            quality = "HD"
        else:
            quality = "SD"
        if not "k2s" in url and not "pixxxels" in url:
            itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url, quality = quality))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

