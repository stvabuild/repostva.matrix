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

from channels import autoplay
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from bs4 import BeautifulSoup

host = 'https://xxxstreams.watch'

list_language = []
list_servers = ['Gounlimited', 'Mixdrop']
list_quality = []
__channel__='streamsXXXeu'
# __comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
# __comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True

#server mixdrop

def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?orderby=date"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/?orderby=views"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/?orderby=likes"))
    itemlist.append(item.clone(title="Mas comentado" , action="lista", url=host + "/?orderby=comments"))
    # itemlist.append(item.clone(title="Canal" , action="categorias", url=host))   #No tiene links

    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s" % (host,texto)
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
    if "Canal" in item.title:
        matches = soup.find('ul', class_='menu').find_all('li')
        del matches[-1]
        del matches[-1]
    else:
        matches = soup.find('div',  id='popular_searches-2').find_all('li')
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text
        thumbnail = ""
        plot = ""
        if title:
            itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
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
    matches = soup.find_all('div', id=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title'].replace("&#8211;", "-")
        thumbnail = elem.img['src']
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='nextpostslink')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='entry-content')
    matches = soup.find_all('iframe')
    for elem in matches:
        url = elem['src']
        itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    autoplay.start(itemlist, item)
    return itemlist

