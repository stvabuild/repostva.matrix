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

canonical = {
             'channel': 'porndoe', 
             'host': config.get_setting("current_host", 'porndoe', default=''), 
             'host_alt': ["https://porndoe.com"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host +"/videos"))
    itemlist.append(Item(channel=item.channel, title="Exclusivos" , action="lista", url=host + "/category/74/premium-hd"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/videos?sort=views-down"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="lista", url=host + "/videos?sort=likes-down"))
    itemlist.append(Item(channel=item.channel, title="Mas largo" , action="lista", url=host + "/videos?sort=duration-down"))
    itemlist.append(Item(channel=item.channel, title="PornStar" , action="categorias", url=host + "/pornstars"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/channels?sort=ranking"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories?sort=name"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search?keywords=%s" % (host,texto)
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
    data1 = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|amp;", "", data1)
    if "channels" in item.url:
        data = scrapertools.find_single_match(data, '<div class="channels-list">(.*?)</section>')
        patron  = '<div>(.*?)</div>'
    else:
        patron  = 'class="ctl-item">(.*?)</p>'
    if "pornstars" in item.url:
        patron  = 'class="actors-list-item">(.*?)>Rank'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        cantidad = ""
        scrapedurl = scrapertools.find_single_match(match,'href="([^"]+)"')
        if "/pornstars-profile" in scrapedurl:
            # thumbnail = scrapertools.find_single_match(match,';(https://p.cdn.porndoe.com/image/porn_star/.*?.jpg)')
            cantidad = scrapertools.find_single_match(match,'<span class="-grow">([^<]+)<')
            cantidad = "(%s)" % cantidad
        else:
            scrapedurl = scrapertools.find_single_match(match,'ng-follow="([^"]+)"')
            import base64
            scrapedurl = base64.b64decode(scrapedurl).decode('utf-8')
            scrapedurl = scrapedurl.replace("channel-profile", "channel-profile-videos")
            scrapedurl += "?sort=date-down"
        thumbnail = scrapertools.find_single_match(match,'data-src="([^"]+)"')
        scrapedtitle = ""
        scrapedtitle = scrapertools.find_single_match(match,'title="([^"]+)"')
        if not scrapedtitle:
            scrapedtitle = scrapertools.find_single_match(match,'class="item-title">([^<]+)<').strip()
        if "/category/" in scrapedurl:
            cantidad = scrapertools.find_single_match(match,'<span class="ctl-count">([^<]+)<')
        title = "%s %s" % (scrapedtitle, cantidad)
        scrapedurl = scrapedurl.replace("https://letsdoeit.com", "")
        url = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data1, '<a class="pager-item pager-next"([^>]+)')
    if next_page:
        next_page = scrapertools.find_single_match(next_page, 'href="([^"]+)"')
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    matches = soup.find_all('div', class_='video-item')
    for elem in matches:
        url = elem.a['href']
        if "redirect" in url:
            continue
        title = elem.find('a', class_='video-item-link')['title']
        thumbnail = elem.svg['data-src']
        time = elem['data-duration']
        hd = elem['data-hd']
        vr = elem['data-vr']
        quality = ""
        if "true" in vr: quality = "VR"
        if "true" in hd: quality = "HD"
        url = urlparse.urljoin(host,url)
        title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time,quality,title)
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail,
                                fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='pager-next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
