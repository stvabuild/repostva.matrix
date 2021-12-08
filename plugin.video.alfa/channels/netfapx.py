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

host = 'https://netfapx.com'

# Timming 

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?orderby=newest"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/?orderby=popular"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/?orderby="))
    itemlist.append(item.clone(title="PornStar" , action="catalogo", url=host + "/pornstar/?orderby=popular"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
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


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('article', class_='pinbox')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.img['alt']
        thumbnail = elem.img['src']
        cantidad = elem.find_all("div")[-2]#.text.split("\n")[2]
        cantidad = scrapertools.find_single_match(str(cantidad), '"Videos"/>([^<]+)<').strip()
        title = "%s (%s)" %(stitle,cantidad)
        url = url.replace("pornstar", "videos")
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot,))
    try:
        next_page = soup.find('a', class_='next')['href']
    except:
        next_page = None
    if next_page:
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page.strip()))
    return itemlist
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    soup = soup.find('div', class_='cat-thumb')
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        thumbnail = elem.img['src']
        title = scrapertools.find_single_match(thumbnail, '.*?/02/(.*?)-Porn-Videos.jpg')
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot,))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('article', class_='pinbox')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.img['alt']
        thumbnail = elem.img['src']
        stime = elem.find_all("div")[-2].text.split("\n")[3]
        title = "[COLOR yellow]%s[/COLOR] %s" % (stime.strip(),stitle)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, contentTitle=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot,))
    try:
        next_page = soup.find('a', class_='next')['href']
    except:
        next_page = None
    if next_page:
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page.strip()))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    url = scrapertools.find_single_match(data, 'source: "([^"]+)"')
    itemlist.append(item.clone(action="play", title = "Direto", url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    url = scrapertools.find_single_match(data, 'source: "([^"]+)"')
    itemlist.append(item.clone(action="play", timeout=30, title = url, url=url))
    return itemlist