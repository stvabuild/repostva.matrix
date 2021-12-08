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

from platformcode import config, logger, platformtools
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from bs4 import BeautifulSoup

host = 'https://viralxvideos.es'     #  https://www.xmoviesforyou.tv   https://www.xvideospanish.net


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?filter=latest"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
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
    soup = create_soup(item.url).find('nav')
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        title = elem.text.strip()
        plot = ""
        thumbnail = ""
        if "viralxvideos" in url:
            itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('li', class_='item-pagin is_last')
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
    matches = soup.find_all('article', id=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.video
        if thumbnail:
            thumbnail = thumbnail['poster']
        else:
            thumbnail = elem.img
            if thumbnail:
                thumbnail = thumbnail['data-src']
            else:
                thumbnail = ""
        quality = elem.find('span', class_='hd-video')
        if quality:
            title = "[COLOR red]HD[/COLOR] %s" % title
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.find_next('a')['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def find_tag(tag):
    return tag.has_attr('src')

def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='responsive-player')
    url = soup.find(find_tag)
    # url = soup.find(src=re.compile(r"^http[A-z0-9=\/]+"))
    if url:
        url = url['src']
    if "videos.sh" in url:
        data = httptools.downloadpage(url).data
        url = scrapertools.find_single_match(data,'sources: \[\{src: "([^"]+)"')
    if "cumlouder" in url:
        soup = create_soup(url)
        url = soup.find('source', type='video/mp4')['src']
    if "player-x.php?" in url:
        import base64
        decode = scrapertools.find_single_match(url,'.*?php\?q=([A-z0-9=]+)')
        decode = base64.b64decode(decode).decode("utf8")
        decode = urlparse.unquote(decode)
        url = scrapertools.find_single_match(decode,'src="([^"]+)"')
        if "pornhub" in url:
            url = url.replace("embed/", "view_video.php?viewkey=")
    if "servidores.jpg" in url:
        itemlist = servertools.find_video_items(item.clone(url = item.url, contentTitle = item.title))
        return itemlist
    if url:
        itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    else:
        platformtools.dialog_ok("viralxvideos: Error", "El archivo no existe o ha sido borrado")
        return
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='responsive-player')
    url = soup.find(find_tag)
    # url = soup.find(src=re.compile(r"^http[A-z0-9=\/]+"))
    if url:
        url = url['src']
    if "videos.sh" in url:
        data = httptools.downloadpage(url).data
        url = scrapertools.find_single_match(data,'sources: \[\{src: "([^"]+)"')
    if "cumlouder" in url:
        soup = create_soup(url)
        url = soup.find('source', type='video/mp4')['src']
    if "player-x.php?" in url:
        import base64
        decode = scrapertools.find_single_match(url,'.*?php\?q=([A-z0-9=]+)')
        decode = base64.b64decode(decode).decode("utf8")
        decode = urlparse.unquote(decode)
        url = scrapertools.find_single_match(decode,'src="([^"]+)"')
        if "pornhub" in url:
            url = url.replace("embed/", "view_video.php?viewkey=")
    if "servidores.jpg" in url:
        itemlist = servertools.find_video_items(item.clone(url = item.url, contentTitle = item.title))
        return itemlist
    if url:
        itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    else:
        platformtools.dialog_ok("viralxvideos: Error", "El archivo no existe o ha sido borrado")
        return
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist