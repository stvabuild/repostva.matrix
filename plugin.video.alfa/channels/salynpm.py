# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from platformcode import config, logger, platformtools
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools, tmdb
from bs4 import BeautifulSoup
from channels import autoplay
from channels import filtertools
from channelselector import get_thumb
import codecs

host = 'https://salyn-pm.blogspot.com'

list_language = []
list_servers = ['Amazon', 'Mega', 'Gvideo']
list_quality = []
__channel__='salynpm'
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(item.clone(title="Películas" , action="lista", url=host + "/search/label/Pel%C3%ADcula?&max-results=24"))
    itemlist.append(item.clone(title="Géneros" , action="generos", url=host + "/p/categorias.html"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    
    itemlist.append(item.clone(title="Configurar canal...", text_color="gold", action="configuracion", thumbnail=get_thumb('setting_0.png')))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?q=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def generos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='col')
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        title = elem.text
        url = url.replace("www.salynpm", "salyn-pm.blogspot")
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail ) )
    return itemlist


def create_soup(url):
    logger.info()
    data = httptools.downloadpage(url, ignore_response_code=True).data
    if "document.write" in data:
        data =  scrapertools.find_single_match(data, r"document\.write\('([^']+)'")
        data = codecs.decode(data.replace("\u000D", "\n"), "unicode_escape")
    if not "Error 404" in data:
        data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
        soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    else:
        soup = ""
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='card')
    for elem in matches:
        quality = elem.find('a', class_='firstag__name')
        if quality:
            quality = quality.text
        else:
            quality = ""
        url = elem.find('h2').a['href']
        title = elem.find('h2').text
        thumbnail = elem.img['src']
        year = '-'
        contentTitle = title
        if quality:
            title = title + " [COLOR red]" + quality + "[/COLOR]"

        itemlist.append(item.clone(action="findvideos", title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, contentTitle = contentTitle,
                              quality=quality, infoLabels={'year':year}))

    tmdb.set_infoLabels(itemlist, True)

    current_page = scrapertools.find_single_match(item.url, "PageNo=(\d+)")
    base_next_page = soup.find('i', class_='fas fa-arrow-right')
    if base_next_page:
        base_next_page = base_next_page.parent['href']
    num = len(itemlist)
    if not current_page and num >= 24 :
        next_page = base_next_page.replace("&start=24", "").replace("&by-date=false", "#PageNo=2")
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    if "search?q=" in item.url:
        next_page = base_next_page
        if num >= 20:
            itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    else:
        base_next_page = base_next_page.replace("&start=24", "").replace("&by-date=false", "")
        if current_page:
            next = str(int(current_page) + 1)
            next_page = base_next_page.replace("PageNo=%s" % current_page, "PageNo=%s" % next)
            itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    audios = ["VOSE","LAT"]
    listed = []
    soup = create_soup(item.url)
    descargas = ""
    if soup.find(src=re.compile("salynpm-links.")):
        descargas = soup.find(src=re.compile("salynpm-links."))['src']
    if soup.find(href=re.compile("salynpm-links.")):
        descargas = soup.find(href=re.compile("salynpm-links."))['href']
    if descargas:
        descargas = create_soup(descargas)
        data = descargas.find('div', class_='post-entry')
        matches = data.find_all('a')
        for elem in matches:
            url = elem['href']
            url = codecs.decode(url,"unicode-escape")
            url = url.replace("?download=1", "").replace("dropboxusercontent", "dropbox").replace("/dl.dropbox", "/www.dropbox")
            if url != "" and url not in listed:
                listed.append(url)
    online = soup.find_all(type='video/mp4')
    codigo = soup.find(string=re.compile("document.write"))
    if codigo:
        codigo = scrapertools.find_single_match(codigo, r"document\.write\(unescape\('([^']+)'")
        codigo = codecs.decode(codigo.replace("%", ""), "hex")
        codigo = BeautifulSoup(codigo, "html5lib", from_encoding="utf-8")
        online = codigo.find_all(type='video/mp4')
    if online:
        for elem in online:
            url = elem['src']
            if "bit.ly" in url:
                url = httptools.downloadpage(url, follow_redirects=False).headers["location"]
            url = codecs.decode(url,"unicode-escape")
            url = url.replace("?download=1", "").replace("dropboxusercontent", "dropbox").replace("/dl.dropbox", "/www.dropbox")
            if url != "" and url not in listed:
                listed.append(url)
    for url in listed:
        if not "bit.ly" in url and not "https://archive.org/download/salynpm" in url:
            itemlist.append(item.clone(action="play", title = "%s", language=audios, url = url ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para Filtrar enlaces
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' and not "/episodios/" in item.url :
        itemlist.append(item.clone(action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle)) 
    return itemlist

