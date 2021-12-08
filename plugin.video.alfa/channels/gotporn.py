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

host = 'https://www.gotporn.com'   

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?src=mn:mr&page=1"))
    itemlist.append(item.clone(title="Mejor valorados" , action="lista", url=host + "/top-rated?page=1"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/most-viewed?page=1"))
    itemlist.append(item.clone(title="Longitud" , action="lista", url=host + "/longest?page=1"))

    itemlist.append(item.clone(title="Canal" , action="catalogo", url=host + "/channels?page=1"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/results?search_query=%s" % (host, texto)
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
    soup = create_soup(item.url).find('ul', class_='categories-list')
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        title = elem.find('span', class_='text').text.strip()
        cantidad = elem.find('span', class_='num').text.strip()
        title = "%s %s" % (title,cantidad)
        url += "?page=1&amp;src=mn:mr"
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=thumbnail) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='channel-card')
    for elem in matches:
        url = elem.a['href']
        thumbnail = elem.img['src']
        title = elem.img['alt']
        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail) )
    next_page = soup.find('link', rel='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def create_soup(url, post=None, unescape=False):
    logger.info()
    if post:
        data = httptools.downloadpage(url, post=post).data
        data = scrapertools.find_single_match(data, '"tpl":"([^&@@]+)')
        data = data.replace("\\n", "").replace("\\", "")
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
    if item.post:
        soup = create_soup(item.url, item.post)
        offset = item.offset
    else:
        soup = create_soup(item.url)
    matches = soup.find_all('li', class_='poptrigger')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['src']
        if ".gif" in thumbnail:
            thumbnail = elem.img['data-src']
        time = elem.find('span', class_='duration').text.strip()
        quality = elem.find('h3', class_='video-thumb-title  hd')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot,))
    next_page = soup.find('link', rel='next')
    next = soup.find('button', id='show-more-videos-btn')
    if next:
        total = next.find('span', id='remaining-video-num').text
        offset= 41
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    if "/channels/" in item.url:
        if next:
            next_page = "https://www.gotporn.com/channels/%s/get-more-videos " % next['data-id']
        else:
            id = scrapertools.find_single_match(item.url, 'https://www.gotporn.com/channels/(\d+)')
            next_page = "https://www.gotporn.com/channels/%s/get-more-videos " % id
        post = {"offset": "%s"  % offset}
        offset += 15
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page, post=post, offset=offset) )
    return itemlist


def findvideos(item):
    logger.info(item)
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # itemlist = servertools.find_video_items(item.clone(url = item.url, contentTitle = item.title))
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
