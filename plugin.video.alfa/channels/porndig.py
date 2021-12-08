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

host = 'https://www.porndig.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", value="date",
                               category = "", offset=""))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", value="views",
                               category = "", offset=""))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", value="rating",
                               category = "", offset=""))
    itemlist.append(item.clone(title="Mas comentado" , action="lista", value="comments",
                               category = "", offset=""))
    itemlist.append(item.clone(title="Mas metraje" , action="lista", value="duration",
                               category = "", offset=""))
    itemlist.append(item.clone(title="PornStar" , action="pornstar", url="/pornstars/load_more_pornstars",
                               value="likes", offset=""))
    itemlist.append(item.clone(title="Canal" , action="pornstar", url="/studios/load_more_studios",
                               value="video_views", offset=""))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/video/"))
    # itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist

# FALLA 
def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search?q=%s" % (host,texto)
    item.texto = texto
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
    matches = soup.find('div', class_='filter_category_select_wrapper').find_all('option')
    for elem in matches:
        category = elem['value']
        title = elem.text
        if category:
            itemlist.append(item.clone(title=title , action="lista", value="date",
                                       category=category, offset=""))
    return itemlist

def create_soup(url, post=None, unescape=False):
    logger.info()
    if post:
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        data = httptools.downloadpage(url, post=post, headers=headers).data
        data = data.replace("\\n", " ").replace("\\t", "").replace("\\", "")
    else:
        data = httptools.downloadpage(url).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def pornstar(item):
    logger.info()
    itemlist = []
    if not item.offset:
        offset = 0
    else:
        offset = item.offset
    if "pornstar" in item.url:
        posturl = "https://www.porndig.com/pornstars/load_more_pornstars"
        post = "main_category_id=1&type=pornstar&name=top_pornstars&filters[filter_type]=%s&offset=%s" % (item.value,offset)
    else:
        posturl = "https://www.porndig.com/studios/load_more_studios"
        post = "main_category_id=1&type=studio&name=top_studios&filters[filter_type]=%s&offset=%s" % (item.value,offset)
    soup = create_soup(posturl, post)
    matches = soup.find_all('div', class_='showcase_item_wrapper')
    for elem in matches:
        value = elem['id'].replace("_", "")
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        cantidad = elem.find('div', class_='showcase_views').text.strip()
        if cantidad:
            title = "%s (%s)" % (title, cantidad)
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url, plot=plot,
                               fanart=thumbnail, thumbnail=thumbnail, value=value, offset=""))
    next_page = scrapertools.find_single_match(str(soup), '"has_more":(true)')
    if next_page:
        offset += 30 
        itemlist.append(item.clone(action="pornstar", title="[COLOR blue]Página Siguiente >>[/COLOR]", offset=offset ) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    if not item.offset:
        offset = 0
    else:
        offset = item.offset
    posturl = "https://www.porndig.com/posts/load_more_posts"
    if item.post:
        post = item.post
    if "pornstars" in item.url:
        post = "main_category_id=1&type=post&name=pornstar_related_videos&filters[filter_type]=ctr&filters[filter_period]=&filters[filter_quality][]=270&content_id=%s&offset=%s" % (item.value,offset)
    else:
        post = "main_category_id=1&type=post&name=multifilter_videos&filters[filter_type]=%s&filters[filter_period]=month&category_id[]=%s&offset=%s" % (item.value,item.category,offset)
    if "studio" in item.url:
        post = "main_category_id=1&type=post&name=studio_related_videos&filters[filter_type]=ctr&filters[filter_period]=&filters[filter_quality][]=270&content_id=%s&offset=%s" % (item.value,offset)
    if "search" in item.url:
        post = "main_category_id=1&type=post&name=search_posts&search=%s&offset=%s" % (item.texto, offset)
    soup = create_soup(posturl, post)
    matches = soup.find_all('section', class_='video_item_medium')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.img['alt']
        thumbnail = elem.img['data-src']
        stime = elem.find('div', class_='bubble').text.strip()
        quality = elem.find('i', class_='pull-right')['class'][1].replace("icon-ic_19_qlt_", "")
        if stime:
            title = "[COLOR yellow]%s[/COLOR] %s" % (stime,stitle)
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (stime,stitle)
        url = urlparse.urljoin(host,url)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, plot=plot,
                               fanart=thumbnail, thumbnail=thumbnail, contentTitle=title ))
    next_page = scrapertools.find_single_match(str(soup), '"has_more":(true)')
    if next_page:
        if "name=all_videos" in post:
            offset += 50 
        else:
            offset += 30 
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", offset=offset ) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', class_='video_download_wrapper').find_all('a', class_='post_download_link clearfix')
    for elem in matches:
        url = elem['href']
        quality = url[-4:]
        url = httptools.downloadpage(url, headers={"referer": item.url}, follow_redirects=False).headers["location"]
        itemlist.append(item.clone(action="play", title=quality, contentTitle = item.title, url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', class_='video_download_wrapper').find_all('a', class_='post_download_link clearfix')
    for elem in matches:
        url = elem['href']
        quality = url[-5:].replace("_", "")
        url = httptools.downloadpage(url, headers={"referer": item.url}, follow_redirects=False).headers["location"]
        itemlist.append([quality, url])
    return itemlist

