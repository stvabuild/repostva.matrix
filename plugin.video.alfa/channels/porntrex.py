# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
    import urllib.parse as urllib
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido
    import urllib

import re

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import config, logger

host = "https://www.porntrex.com"

def mainlist(item):
    logger.info()
    itemlist = []

    config.set_setting("url_error", False, "porntrex")
    itemlist.append(item.clone(action="lista", title="Nuevos Vídeos", url=host + "/latest-updates/"))
    itemlist.append(item.clone(action="lista", title="Mejor Valorados", url=host + "/top-rated/"))
    itemlist.append(item.clone(action="lista", title="Más Vistos", url=host + "/most-popular/"))
    itemlist.append(item.clone(action="categorias", title="Modelos", url=host + "/models/?sort_by=avg_videos_popularity"))
    itemlist.append(item.clone(action="categorias", title="Canal", url=host + "/channels/"))
    itemlist.append(item.clone(action="categorias", title="Listas", url=host + "/playlists/"))
    itemlist.append(item.clone(action="categorias", title="Categorías", url=host + "/categories/?sort_by=title"))
    itemlist.append(item.clone(title="Buscar...", action="search"))
    itemlist.append(item.clone(action="configuracion", title="Configurar canal...", text_color="gold", folder=False))

    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = "%s/search/%s/" % (host, texto.replace("+", "-"))
    item.extra = texto
    try:
        return lista(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = get_data(item.url)
    data = scrapertools.find_single_match(data, '<div class="main-container">(.*?)</html>')
    # Extrae las entradas
    if "/channels/" in item.url:
        patron = '<div class="video-item   ">.*?<a href="([^"]+)" title="([^"]+)".*?src="([^"]+)".*?<li>([^<]+)<'
    elif "/playlists/" in item.url:
        patron = '<div class="item ">.*?<a href="([^"]+)" title="([^"]+)".*?data-original="([^"]+)".*?<div class="totalplaylist">([^<]+)<'
    else:
        patron = '<a class="item" href="([^"]+)" title="([^"]+)".*?src="([^"]+)".*?<div class="videos">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, videos in matches:
        scrapedurl = urlparse.urljoin(host, scrapedurl)
        if not scrapedthumbnail.startswith("https"):
            scrapedthumbnail = "https:%s" % scrapedthumbnail
            scrapedthumbnail = scrapedthumbnail.replace(" " , "%20")
        if videos:
            scrapedtitle = "%s  (%s)" % (scrapedtitle, videos)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail))
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
    if "#" in next_page:
        next_page = scrapertools.find_single_match(data, '<li class="next">.*?data-parameters="([^"]+)">')
        next_page = next_page.replace(":", "=").replace(";", "&").replace("+from_albums", "")
        next_page = "?%s" % next_page
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    # Descarga la pagina 
    data = get_data(item.url)
    action = "play"
    if config.get_setting("menu_info", "porntrex"):
        action = "menu_info"
    # Quita las entradas, que no son private <div class="video-preview-screen video-item thumb-item private "
    if "playlists" in item.url:
        patron = '<div class="video-item item  ".*?'
    else:
        patron = '<div class="video-preview-screen video-item thumb-item  ".*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src="([^"]+)"\s*alt="([^"]+)".*?'
    patron += '<span class="quality">([^<]+)<.*?'
    patron += '</i>([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, quality, duration in matches:
        if not scrapedthumbnail.startswith("https"):
            scrapedthumbnail = "https:%s" % scrapedthumbnail
        scrapedtitle = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (duration, quality, scrapedtitle)
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, 
                              contentThumbnail=scrapedthumbnail, fanart=scrapedthumbnail, contentTitle = scrapedtitle))
    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
    if "#" in next_page:
        next_page = scrapertools.find_single_match(data, '<li class="next">.*?data-parameters="([^"]+)">')
        next_page = next_page.replace(":", "=").replace(";", "&").replace("+from_albums", "")
        next_page = "?%s" % next_page
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = get_data(item.url)
    patron = '(?:video_url|video_alt_url[0-9]*):\s*\'([^\']+)\'.*?'
    patron += '(?:video_url_text|video_alt_url[0-9]*_text):\s*\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    scrapertools.printMatches(matches)
    for url, quality in matches:
        quality = quality.replace(" HD" , "").replace(" 4k", "")
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    # if item.extra == "play_menu":
        # return itemlist, data
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = get_data(item.url)
    patron = '(?:video_url|video_alt_url[0-9]*):\s*\'([^\']+)\'.*?'
    patron += '(?:video_url_text|video_alt_url[0-9]*_text):\s*\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    scrapertools.printMatches(matches)
    for url, quality in matches:
        quality = quality.replace(" HD" , "").replace(" 4k", "")
        itemlist.append(['.mp4 %s [directo]' % quality, url])
    if item.extra == "play_menu":
        return itemlist, data
    return itemlist


def menu_info(item):
    logger.info()
    itemlist = []
    video_urls, data = play(item.clone(extra="play_menu"))
    itemlist.append(item.clone(action="play", title="Ver -- %s" % item.title, video_urls=video_urls))
    matches = scrapertools.find_multiple_matches(data, '<img class="thumb lazy-load" src="([^"]+)"')
    for i, img in enumerate(matches):
        if i == 0:
            continue
        if not img.startswith("https"):
            img = "https:%s" % img
        title = "Imagen %s" % (str(i))
        itemlist.append(item.clone(action="", title=title, thumbnail=img, fanart=img))
    return itemlist


def get_data(url_orig):
    try:
        if config.get_setting("url_error", "porntrex"):
            raise Exception
        response = httptools.downloadpage(url_orig)
        if not response.data or "urlopen error [Errno 1]" in str(response.code):
            raise Exception
    except:
        config.set_setting("url_error", True, "porntrex")
        import random
        server_random = ['nl', 'de', 'us']
        server = server_random[random.randint(0, 2)]
        url = "https://%s.hideproxy.me/includes/process.php?action=update" % server
        post = "u=%s&proxy_formdata_server=%s&allowCookies=1&encodeURL=0&encodePage=0&stripObjects=0&stripJS=0&go=" \
               % (urllib.quote(url_orig), server)
        while True:
            response = httptools.downloadpage(url, post, follow_redirects=False)
            if response.headers.get("location"):
                url = response.headers["location"]
                post = ""
            else:
                break
    return response.data
