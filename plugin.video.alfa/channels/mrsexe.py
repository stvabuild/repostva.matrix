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

host = 'https://www.mrsexe.com'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/videos/most-viewed/"))
    itemlist.append(item.clone(title="Mas largo" , action="lista", url=host + "/videos/longues/"))
    itemlist.append(item.clone(title="PornStar" , action="catalogo", url=host + "/filles/"))
    itemlist.append(item.clone(title="Series" , action="catalogo", url=host + "/series.html"))

    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?search=%s" % (host,texto)
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
    soup = create_soup(item.url).find('option', string='Catégories').parent
    matches = soup.find_all('option')
    for elem in matches:
        url = elem['value']
        title = elem.text.strip()
        url = urlparse.urljoin(item.url,url)
        thumbnail = ""
        plot = ""
        if not "Catégories" in title:
            itemlist.append(item.clone(action="lista", title=title, url=url,
                                  thumbnail=thumbnail , plot=plot) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('h1').find_parent('div')
    matches = soup.find('ul', class_='thumb-list')
    for elem in matches.find_all('li'):
        url = elem.a['href']
        text = elem.find('div', class_='infos').text.strip().split("\n")
        thumbnail = elem.img['src']
        if elem.figcaption:
            cantidad = text[0]
            title = elem.figcaption.text.strip()
        else:
            cantidad = text[1]
            title = text[0]
        if cantidad:
            title = "%s (%s)" % (title,cantidad)
        url = urlparse.urljoin(item.url,url)
        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
        plot = ""
        if not "Catégories" in title:
            itemlist.append(item.clone(action="lista", title=title, url=url,
                                  thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('a', string="suivant")
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    soup = create_soup(item.url).find('h1').find_parent('div')
    matches = soup.find('ul', class_='thumb-list').find_all('li')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('figcaption').text.strip().split("\n")
        thumbnail = elem.img['src']
        # time = elem.find('span', class_='duration').text.strip()
        time = title[0]
        title = title[1]
        quality = elem['class']
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        url = urlparse.urljoin(item.url,url)
        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', string="suivant")
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


# https://www.mrsexe.com/classiques/streaming/une-metisse-blonde-se-fait-taper-dans-la-chatte-en-foret-1972.html
# <script type='text/javascript' language='javascript' src='/inc/clic.php?video=12654_3_1500&cat=mrsexe&site=lfapc'></script>
# https://www.mrsexe.com/inc/clic.php?video=12654_3_1500&cat=mrsexe&site=lfapc
# V1972.src("https://dlms1.mrsexe.com/64026dff5e132678486f070f9d8a7b77.mp4");


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, "src='(/inc/clic.php\?video=[^']+)'")
    url = urlparse.urljoin(host,url)
    data = httptools.downloadpage(url).data
    url = scrapertools.find_single_match(data, '.src\("([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, "src='(/inc/clic.php\?video=[^']+)'")
    url = urlparse.urljoin(host,url)
    data = httptools.downloadpage(url).data
    url = scrapertools.find_single_match(data, '.src\("([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
