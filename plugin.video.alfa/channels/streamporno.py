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
from channels import filtertools
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['gounlimited']

host = 'https://pornstreams.tv'     #streamsXXXeu  https://xxxstreams.watch
                                
# Links caidos en canal y categorias


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevas" , action="lista", url=host))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
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
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li id="menu-item-.*?<a href="([^"]+)">([^"]+)</a>'
    if item.title == "Categorias":
        itemlist.append(item.clone(title="Big Tits" , action="lista", url=host + "/?s=big+tits"))
        patron  = '<li class="cat-item.*?<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist

# <article id="post-200925" class="post-200925 post type-post status-publish format-standard has-post-thumbnail hentry category-pornstreams tag-nubiles"><div class="featured-image"> 
# <a href="https://pornstreams.eu/nubiles-madison-love-thinking-of-you/" title="Nubiles &#8211; Madison Love &#8211; Thinking Of You">
# <img width="622" height="350" src="https://pornstreams.eu/wp-content/uploads/2021/02/Nubiles-Madison-Love-Thinking-Of-You.jpg" class="attachment-colormag-featured-image size-colormag-featured-image wp-post-image" alt="Nubiles   Madison Love   Thinking Of You" srcset="https://pornstreams.eu/wp-content/uploads/2021/02/Nubiles-Madison-Love-Thinking-Of-You.jpg 622w, https://pornstreams.eu/wp-content/uploads/2021/02/Nubiles-Madison-Love-Thinking-Of-You-300x169.jpg 300w" sizes="(max-width: 622px) 100vw, 622px" title="Nubiles Madison Love Thinking Of You" /></a></div><div class="article-content clearfix"><div class="above-entry-meta"><span class="cat-links"><a href="https://pornstreams.eu/category/pornstreams/"  rel="category tag">Pornstreams</a>&nbsp;</span></div><header class="entry-header"><h2 class="entry-title"> <a href="https://pornstreams.eu/nubiles-madison-love-thinking-of-you/" title="Nubiles &#8211; Madison Love &#8211; Thinking Of You">Nubiles &#8211; Madison Love &#8211; Thinking Of You</a></h2></header><div class="below-entry-meta"> <span class="posted-on"><a href="https://pornstreams.eu/nubiles-madison-love-thinking-of-you/" title="1:08 pm" rel="bookmark"><i class="fa fa-calendar-o"></i> <time class="entry-date published" datetime="2021-02-06T13:08:45+00:00">February 6, 2021</time></a></span> <span class="byline"><span class="author vcard"><i class="fa fa-user"></i><a class="url fn n"
 # href="https://pornstreams.eu/author/admin/"
 # title="admin">admin</a></span></span> <span class="tag-links"><i class="fa fa-tags"></i><a href="https://pornstreams.eu/tag/nubiles/" rel="tag">Nubiles</a></span></div><div class="entry-content clearfix"> <a class="more-link" title="Nubiles &#8211; Madison Love &#8211; Thinking Of You" href="https://pornstreams.eu/nubiles-madison-love-thinking-of-you/"><span>Read more</span></a></div></div></article>


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<article id=.*?<a href="([^"]+)" title="([^"]+)">.*?src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append(item.clone(action="findvideos" , title=title , url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'<a class="nextpostslink" rel="next" href="([^"]+)">&raquo;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist = servertools.find_video_items(item.clone(url = item.url, contentTitle = item.title))
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

