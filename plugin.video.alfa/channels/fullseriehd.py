# -*- coding: utf-8 -*-
# -*- Channel FullSerieHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channels import filtertools
from bs4 import BeautifulSoup
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from channels import autoplay
from platformcode import config, logger
from channelselector import get_thumb


host = 'https://fullseriehd.com/'

IDIOMAS = {'Subtitulado': 'VOSE', 'Latino':'LAT', 'Castellano':'CAST'}
list_language = list(IDIOMAS.values())
list_servers = ['okru', 'fembed', 'gvideo', 'mega']
list_quality = ['HD-1080p', 'HD-720p', 'Cam']


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html.parser", from_encoding="utf-8")

    return soup

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu',
                         thumbnail=get_thumb('movies', auto=True), type=1))

    itemlist.append(Item(channel=item.channel, title='Series',  action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True), type=2))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Novedades", action="list_all", 
                         url=host + item.title.lower(),
                         thumbnail=get_thumb("newest", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=host,
                         thumbnail=get_thumb("genres", auto=True), type=item.type))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section", url=host,
                         thumbnail=get_thumb("alphabet", auto=True), type=item.type))

    itemlist.append(Item(channel=item.channel, title="Por Año", action="year",
                         thumbnail=get_thumb("year", auto=True), type=item.type))


    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()
    if item.type:
        item.url += '?tr_post_type=%s' % item.type
    soup = create_soup(item.url)
    matches = soup.find("ul", class_="MovieList NoLmtxt Rows AX A06 B04 C03 E20")

    if not matches:
        return itemlist

    for elem in soup.find_all("article"):
        url = elem.a["href"]
        title = fix_title(elem.a.h3.text)
        try:
            thumb = re.sub(r'-\d+x\d+.jpg', '.jpg', elem.find("img")["data-src"])
        except:
            thumb = elem.find("img")["src"]

        
        year = ''
        quality = ''
        if not "-serie-" in url:
            quality = elem.find("span", class_="Qlty").text
            try:
                year = elem.find("span", class_="Year").text
            except:
                pass

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})

        if "-serie-" in url:
            new_item.contentSerieName = title
            new_item.action = "seasons"
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"
            new_item.quality = quality

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        next_page = soup.find("a", class_="next page-numbers")["href"]
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist

def year(item):
    import datetime
    logger.info()

    itemlist = list()
    
    now = datetime.datetime.now()
    c_year = now.year + 1
        
    l_year = c_year - 21
    year_list = list(range(l_year, c_year))

    for year in year_list:
        year = str(year)
        url = '%s?s=trfilter&trfilter=1&tr_post_type=%s&years[]=%s,' % (host, item.type, year)
            
        itemlist.append(Item(channel=item.channel, title=year, url=url,
                                 action="list_all"))
    itemlist.reverse()
    return itemlist

def section(item):
    logger.info()
    import string

    itemlist = list()

    if item.title == "Generos":
        soup = create_soup(item.url).find("div", id="categories-2")
        for elem in soup.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text
            itemlist.append(Item(channel=item.channel, title=title, action="list_all",
                                 url=url, type=item.type))

    elif item.title == "Alfabetico":
        url = '%sletter/0-9/?tr_post_type=%s' % (host, item.type)
        itemlist.append(Item(channel=item.channel, title='#', action="alpha_list",
                                 url=url, type=item.type))

        for l in string.ascii_uppercase:
            url = '%sletter/%s/?tr_post_type=%s' % (host, l.lower(), item.type)
            title = l
            itemlist.append(Item(channel=item.channel, title=title, action="alpha_list",
                                 url=url, type=item.type))

    return itemlist


def alpha_list(item):
    logger.info()

    itemlist = list()
    
    data = create_soup(item.url)
    soup = data.find("tbody")
    
    if not soup:
        return itemlist
    for elem in soup.find_all("tr"):
        info = elem.find("td", class_="MvTbTtl")
        thumb = elem.find("td", class_="MvTbImg").a.img["src"]
        url = info.a["href"]
        title = info.a.text.strip()
        
        year = ''
        quality = ''
        if '/pelicula/' in url:
            quality = elem.find("span", class_="Qlty").text
            try:
                year = elem.find("td", text=re.compile(r"\d{4}")).text
            except:
                pass            

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})

        if '/pelicula/' in url:
            new_item.contentTitle = title
            new_item.action = "findvideos"
            new_item.quality = quality
        else:
            new_item.contentSerieName = title
            new_item.action = "seasons"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        next_page = data.find("a", class_="next page-numbers")["href"]
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find_all("div", class_="Wdgt AABox")

    infoLabels = item.infoLabels
    if len(soup) == 1:
        item.infoLabels["season"] = 1
        item.action = 'episodesxseason'
        return episodesxseason(item)
    for elem in soup:
        season = elem.find("div", class_="AA-Season")["data-tab"]
        title = "Temporada %s" % season
        infoLabels["season"] = season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseason',
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.extra:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName
                             ))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find_all("div", class_="Wdgt AABox")
    infoLabels = item.infoLabels
    season = infoLabels["season"]

    for elem in soup:
        if elem.find("div", class_="AA-Season")["data-tab"] == str(season):
            epi_list = elem.find_all("tr")
            for epi in epi_list:
                url = epi.a["href"]
                epi_num = epi.find("span", class_="Num").text
                epi_name = epi.find("td", class_="MvTbTtl").a.text
                infoLabels["episode"] = epi_num
                title = "%sx%s - %s" % (season, epi_num, epi_name)

                itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                                     infoLabels=infoLabels))
            break
    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.extra and season == 1:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName
                             ))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    #servers = {'opciÃ³n 1': 'okru', 'opción 2': 'fembed'}
    data = create_soup(item.url)
    soup = data.find("ul", class_="TPlayerNv")
    if not soup:
        return itemlist
    infoLabels = item.infoLabels
    for btn in soup.find_all("li"):
        opt = btn["data-tplayernv"]
        srv = btn.span.text.lower()
        if 'opc' in srv:
            if ' 2' in srv:
                srv = 'fembed'
            else:
                srv = 'okru'
        elif 'premi' in srv:
            srv = 'gvideo'
        
        info = btn.span.findNext('span').text.split(' - ')
        lang = IDIOMAS.get(info[0], info[0])
        quality = info[1]

        itemlist.append(Item(channel=item.channel, title=srv, url=item.url, action='play', server=srv, opt=opt,
                            infoLabels=infoLabels, language=lang, quality=quality))
    
    downlist = get_downlist(item, data)
    itemlist.extend(downlist)
    
    itemlist = sorted(itemlist, key=lambda i: (i.language, i.server))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def play(item):
    logger.info()
    itemlist = list()

    if not item.opt:
        if host in item.url:
            item.url = httptools.downloadpage(item.url, ignore_response_code=True).url
        
        itemlist.append(item.clone(url=item.url, server=""))
        itemlist = servertools.get_servers_itemlist(itemlist)
        
        return itemlist

    soup = create_soup(item.url).find("div", class_="TPlayerTb", id=item.opt)
    url = scrapertools.find_single_match(str(soup), 'src="([^"]+)"')
    url = re.sub("amp;|#038;", "", url)
    url = create_soup(url).find("div", class_="Video").iframe["src"]
    if 'Gdri.php' in url:
        url = scrapertools.find_single_match(url, 'v=([A-z0-9-_=]+)')
        url = 'https://drive.google.com/file/d/%s/preview' % url
    itemlist.append(item.clone(url=url, server=""))
    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        if texto != '':
            item.url += texto
            return list_all(item)
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def fix_title(title):
    title = re.sub(r'\((.*)', '', title)
    title = re.sub(r'\[(.*?)\]', '', title)
    return title

def get_downlist(item, data):
    import base64
    logger.info()

    downlist = list()
    servers = {'drive': 'gvideo', '1fichier': 'onefichier'}
    
    soup = data.find("tbody").find_all("tr")
    infoLabels = item.infoLabels
    
    for tr in soup:
        burl = tr.a["href"].split('?l=')[1]
        try:
            for x in range(7):
                durl = base64.b64decode(burl).decode('utf-8')
                burl = durl
        except:
            url = burl

        info = tr.span.findNext('span')
        info1 = info.findNext('span')
        
        srv = info.text.strip().lower()
        srv = servers.get(srv, srv)
        
        lang = info1.text.strip()
        lang = IDIOMAS.get(lang, lang)
        
        quality = info1.findNext('span').text

        downlist.append(Item(channel=item.channel, title=srv, url=url, action='play', server=srv,
                            infoLabels=infoLabels, language=lang, quality=quality))

    return downlist

