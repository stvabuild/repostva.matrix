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

host = 'https://spankbang.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos", action="lista", url= host + "/new_videos/"))
    itemlist.append(item.clone(title="Mas valorados", action="lista", url=host + "/trending_videos/"))
    itemlist.append(item.clone(title="Mas vistos", action="lista", url= host + "/most_popular/"))
    itemlist.append(item.clone(title="Pornstars" , action="catalogo", url=host + "/pornstars"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/s/%s/" % (host, texto)
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
    soup = create_soup(item.url).find('main', id='container')
    matches = soup.find_all('a', class_='image')
    for elem in matches:
        url = elem['href']
        title = elem.img['title']
        thumbnail = elem.img['src']
        cantidad = elem.find('span', class_='videos')
        if cantidad:
            title = "%s (%s)" %(title, cantidad.text)
        url =  urlparse.urljoin(host,url)
        url += "?order=new"
        thumbnail =  urlparse.urljoin(host,thumbnail)
        itemlist.append(item.clone(action="lista", title=title , url=url , 
                              thumbnail=thumbnail, fanart=thumbnail) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page ) )

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='categories')
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        title = elem.text
        thumbnail = elem.img['src']
        url = url.replace("?o=hot", "?o=new")
        url =  urlparse.urljoin(item.url,url)
        thumbnail =  urlparse.urljoin(item.url,thumbnail)
        itemlist.append(item.clone(action="lista", title=title , url=url , 
                              thumbnail=thumbnail, fanart=thumbnail) )
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data
        data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('main', id='container')
    matches = soup.find_all('div', id=re.compile(r"^v_id_\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['data-src']
        time = elem.find('span', class_='l')
        quality = elem.find('span', class_='h')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time.text,quality.text,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time.text,title)
        url =  urlparse.urljoin(item.url,url)
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title , url=url, thumbnail=thumbnail, 
                              fanart=thumbnail, contentTitle=title) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page ) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

