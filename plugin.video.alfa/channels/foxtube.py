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
from channels import cumlouder

host = 'https://www.foxtube.com' #https://www.muyzorras.com


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Ultimos" , action="lista", url=host))
    itemlist.append(item.clone(title="PornStar" , action="catalogo", url=host + '/pornstars/'))
    itemlist.append(item.clone(title="Canal" , action="catalogo", url=host + '/channels/'))
    
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/tags/%s" % (host, texto)
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
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<article>.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img.*?src="([^"]+)".*?'
    patron += 'alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle  in matches:
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        thumbnail = scrapedthumbnail.replace("https","http") + "|Referer=%s/pornstars/" %host
        plot = ""
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=plot) )
    next_page = scrapertools.find_single_match(data,'<a rel="next" href="([^"]+)">&gt')
    if not next_page:
        next_page = scrapertools.find_single_match(data,'<span class="">.*?href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li><a href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    if "channels" in item.url:
        canal = ""
        data = httptools.downloadpage(item.url).data
        id = scrapertools.find_single_match(data,'<section id="contenedor".*?a href="https://www.foxtube.com/pu/(\d+)')
        canal = scrapertools.find_single_match(data,'path : \'([^\']+)\'')
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        post = {'path': '%s' %canal, 'order_vid': 'uv'} 
        item.url = "https://www.foxtube.com/users/get/%s/videos/1/" % id
        data = httptools.downloadpage(item.url, post=post, headers=headers).data
    if "users" in item.url:
        canal= item.canal
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        post = {'path': '%s' %canal, 'order_vid': 'uv'} 
        data = httptools.downloadpage(item.url, post=post, headers=headers).data
    else:
        data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = data.replace("\\n", "").replace("\\", "")
    if "pornstars" in item.url:
        data = scrapertools.find_single_match(data,'<html lang="en">(.*?)>Similar pornstars</h2>')
    patron = '<article>.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img.*?src="([^"]+)".*?'
    patron += 'alt="([^"]+)".*?'
    patron += '<span class="r\w">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
        time = scrapertools.find_single_match(duracion, '<span>([^<]+)</span></span>')
        title = "[COLOR yellow]%s[/COLOR] %s" %(time,scrapedtitle)
        if 'HD' in duracion :
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR]  %s" %(time,scrapedtitle)
        thumbnail = scrapedthumbnail.replace("https","http") + "|Referer=%s/" %host
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data,'<a rel="next" href="([^"]+)">&gt')
    if "pornstars" in item.url or "tags" in item.url:
        next_page = scrapertools.find_single_match(data,'<a href="([^"]+)" rel="next">')
    if "users" in item.url:
        page = scrapertools.find_single_match(item.url, "(.*?/videos)/\d+")
        next_page = scrapertools.find_single_match(data, '<li class="selected">.*?data-pag="(\d+)"')
        if next_page:
            next_page = "%s/%s/" %(page,next_page)
            itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page, canal= canal) )
    else:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    url = ""
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data,'<iframe title="[^"]+" class="lz" data-src="([^"]+)"')
    if "cumlouder" in url:
        item1 = item.clone(url=url)
        itemlist = cumlouder.play(item1)
        return itemlist
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    url = ""
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data,'<iframe title="[^"]+" class="lz" data-src="([^"]+)"')
    if "cumlouder" in url:
        item1 = item.clone(url=url)
        itemlist = cumlouder.play(item1)
        return itemlist
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist