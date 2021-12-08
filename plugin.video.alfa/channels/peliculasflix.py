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

from channels import autoplay
from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, tmdb
from core import servertools, channeltools
from channels import filtertools
from bs4 import BeautifulSoup
from channelselector import get_thumb

SERVER = {'Ok': 'okru','Flixplayer': 'gounlimited', 'gounlimited': 'gounlimited'}
IDIOMAS = {"espana": "CAST", "mexico": "LAT", "usa": "VOSE", "Castellano": "CAST", "Latino": "LAT", "Subtitulado": "VOSE"}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = list(SERVER.values())

__channel__='peliculasflix'

host = 'https://peliculasflix.co'   #  https://peliculasflix.co   https://seriesflix.nu/     https://pelisflix.li     https://mundokaos.net

url1 = "%s/?v=Opciones" %host


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(item.clone(title="Peliculas" , action="lista", url= host + "/ver-peliculas-online/", thumbnail=get_thumb("movies", auto=True)))
    itemlist.append(item.clone(title="Genero" , action="categorias", url= host, thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(item.clone(title="Productora" , action="categorias", url= host))
    itemlist.append(item.clone(title="Alfabetico", action="section", url=host, thumbnail=get_thumb("alphabet", auto=True)))
    itemlist.append(item.clone(title="Buscar...", action="search", thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)
    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = "%s/?s=%s" % (host, texto)
        if texto != "":
            return lista(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    if "Genero" in item.title:
        soup = create_soup(item.url).find("li", id="menu-item-191")
    else:
        soup = create_soup(item.url).find("li", id="menu-item-192")
    matches = soup.find_all("li")
    for elem in matches:
        url = elem.a["href"]
        title = elem.a.text
        itemlist.append(item.clone(action="lista", url=url, title=title))
    if "Genero" in item.title:
        url= "https://peliculasflix.co/genero/marvel/"
        itemlist.append(item.clone(action="lista", url=url, title="MARVEL"))

    return itemlist

def section(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find("ul", class_="AZList")
    for elem in soup.find_all("li"):
        url = elem.a["href"]
        title = elem.a.text
        itemlist.append(item.clone(action="alpha_list", url=url, title=title))

    return itemlist


def alpha_list(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find("tbody")
    if not matches:
        return itemlist
    for elem in matches.find_all("tr"):
        info = elem.find("td", class_="MvTbTtl")
        thumb = elem.img["data-src"]
        # thumb = elem.img["src"]
        url = info.a["href"]
        title = info.a.text.strip()
        year = elem.find_all('td')[4].text
        itemlist.append(item.clone(action="findvideos", url=url, title=title, contentTitle=title, thumbnail=thumb, infoLabels={"year": year} ))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if not config.get_setting('unify') and not channeltools.get_channel_parameters(__channel__)['force_unify']:
        a = len(itemlist)-1
        for i in itemlist:
            if a >= 0:
                title= itemlist[a].contentTitle
                titulo = itemlist[a].title
                titulo = scrapertools.find_single_match(titulo, '(\\[COLOR[^"]+)')
                title = "%s %s" %(title, titulo)
                itemlist[a].title = title
                a -= 1
    next_page = soup.find('a', class_='current')
    if next_page and next_page.find_next_sibling("a"):
        next_page = next_page.find_next_sibling("a")['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="alpha_list", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def create_soup(url, referer=None, post=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    if post:
        data = httptools.downloadpage(url, post=post).data
    else:
        data = httptools.downloadpage(url).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url, referer=host)
    matches = soup.find_all("li", id=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        thumbnail = elem.figure.img['data-src']
        lg = elem.find(class_='Lg').find_all('img')
        language = []
        for l in lg:
            lang = l['data-src']
            lang = scrapertools.find_single_match(lang,'/(\w+).png')
            language.append(IDIOMAS.get(lang, lang))
        year = elem.find(class_='Yr')
        if year:
            year = year.text
        else:
            year = elem.find(class_='Date')
        title = elem.h2.text.strip()
        contentTitle = title
        # quality = elem.find('span', class_='Qlty').text.strip().split()
        # quality = quality[-1]
        if year == '':
            year = '-'
            
        if not config.get_setting('unify') and not channeltools.get_channel_parameters(__channel__)['force_unify']:
            if year != "-":
                title = "%s [COLOR cyan](%s)[/COLOR] [COLOR darkgrey]%s[/COLOR]" % (title,year, language)
            else:
                title = "%s [COLOR darkgrey]%s[/COLOR]" % (title, language)
        else:
            title = title
        itemlist.append(item.clone(action="findvideos", url=url, title=title, contentTitle=contentTitle, thumbnail=thumbnail,
                                   language=language, infoLabels={"year": year} ))
    tmdb.set_infoLabels(itemlist, True)


    if not config.get_setting('unify') and not channeltools.get_channel_parameters(__channel__)['force_unify']:
        a = len(itemlist)-1
        for i in itemlist:
            if a >= 0:
                title= itemlist[a].contentTitle
                titulo = itemlist[a].title
                titulo = scrapertools.find_single_match(titulo, '(\\[COLOR[^"]+)')
                title = "%s %s" %(title, titulo)
                itemlist[a].title = title
                a -= 1
    next_page = soup.find('div', class_='nav-links').find('a', class_='current').find_next_sibling("a")
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist



def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('li', class_='OptionBx')
    serv=[]
    for elem in matches:
        num= elem['data-key']
        id= elem['data-id']
        lang= elem.find('p', class_='AAIco-language').text.split()
        server =  elem.find('p', class_='AAIco-dns').text.strip()
        # quality = elem.find('p', class_='AAIco-equalizer').text.split()
        # quality = quality[-1]
        lang = lang[-1]
        lang = IDIOMAS.get(lang, lang)
        server = SERVER.get(server, server)
        url = "%s//?trembed=%s&trid=%s&trtype=1"  %  (host,num,id)
        if not config.get_setting('unify') and not channeltools.get_channel_parameters(__channel__)['force_unify']:
            title = "[%s] [COLOR darkgrey][%s][/COLOR]" %(server,lang)
        else:
            title = server
        if not "gounlimited" in server:
            itemlist.append(item.clone(action="play", title=title, url=url, server=server, language=lang ))

    itemlist.sort(key=lambda it: (it.language))

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' and not "/episodios/" in item.url :
        itemlist.append(item.clone(action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle)) 
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    logger.debug("ITEM: %s" % item)
    url = create_soup(item.url).find(class_='Video').iframe['src']
    itemlist = servertools.get_servers_itemlist([item.clone(url=url, server="")])
    itemlist = servertools.get_servers_itemlist(itemlist)
    return itemlist

