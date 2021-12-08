# -*- coding: utf-8 -*-
# -*- Channel FullSerieHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re, datetime

from bs4 import BeautifulSoup
from core import httptools, scrapertools, servertools
from core.item import Item
from core import tmdb
from channels import autoplay, filtertools
from platformcode import config, logger
from channelselector import get_thumb


host = 'https://pelishd24.com/'

IDIOMAS = {'Subtitulado': 'VOSE', 'Latino':'LAT', 'Castellano':'CAST'}
list_language = list(IDIOMAS.values())
list_servers = ['okru', 'fembed']
list_quality = ['HD-1080p', 'HD', 'CAM']


def create_soup(url, referer=None, unescape=False):
    logger.info()

    data = httptools.downloadpage(url, headers={'Referer':referer}).data
    
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html.parser", from_encoding="utf-8")

    return soup

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    now = datetime.datetime.now().year

    itemlist.append(Item(channel=item.channel, title="Estrenos", action="list_all", 
                         url=host + '?s=trfilter&trfilter=1&years[]=%s' % now,
                         thumbnail=get_thumb("premieres", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Novedades", action="list_all", 
                         url=host + 'peliculas',
                         thumbnail=get_thumb("newest", auto=True)))

    # itemlist.append(Item(channel=item.channel, title='Series',  action='list_all',
    #                      thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Latino", action="list_all", 
                         url=host + 'peliculas-latino',
                         thumbnail=get_thumb("lat", auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Castellano", action="list_all", 
                         url=host + 'peliculas-castellano',
                         thumbnail=get_thumb("cast", auto=True)))

    itemlist.append(Item(channel=item.channel, title="VOSE", action="list_all", 
                         url=host + 'peliculas-subtitulas',
                         thumbnail=get_thumb("vose", auto=True)))


    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=host,
                         thumbnail=get_thumb("genres", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section", url=host,
                         thumbnail=get_thumb("alphabet", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por Año", action="year",
                         thumbnail=get_thumb("year", auto=True)))


    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist




def list_all(item):
    logger.info()

    itemlist = list()
    
    soup = create_soup(item.url)
    matches = soup.find("ul", class_="MovieList NoLmtxt Rows AX A06 B04 C03 E20")

    if not matches:
        return itemlist

    for elem in soup.find_all("article"):
        url = elem.a["href"]
        #Hay pocas series funcionales y usan otro metodo para findvideos
        if "/serie/" in url:
            continue
        title = fix_title(elem.a.h3.text)
        try:
            thumb = re.sub(r'-\d+x\d+.jpg', '.jpg', elem.find("img")["data-src"])
        except:
            thumb = elem.find("img")["src"]

        
        year = ''
        #quality = ''
        try:
            year = elem.find("span", class_="Year").text
        except:
            pass

        # new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})

        # if "/serie/" in url:
        #     new_item.contentSerieName = title
        #     new_item.action = "seasons"
        # else:
            # new_item.contentTitle = title
            # new_item.action = "findvideos"

        #itemlist.append(new_item)
        itemlist.append(Item(channel=item.channel, title=title, url=url,
                             action="findvideos",contentTitle=title, 
                             thumbnail=thumb, infoLabels={"year": year}))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        next_page = soup.find("a", class_="next page-numbers")["href"]
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist

def year(item):
    
    logger.info()

    itemlist = list()
    
    now = datetime.datetime.now()
    c_year = now.year + 1
        
    l_year = c_year - 21
    year_list = list(range(l_year, c_year))

    for year in year_list:
        year = str(year)
        url = '%s?s=trfilter&trfilter=1&years[]=%s,' % (host, year)
            
        itemlist.append(Item(channel=item.channel, title=year, url=url,
                                 action="list_all"))
    itemlist.reverse()
    return itemlist

def section(item):
    logger.info()
    import string

    itemlist = list()

    if item.title == "Generos":
        soup = create_soup(item.url).find("li", id="menu-item-242")
        for elem in soup.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text
            itemlist.append(Item(channel=item.channel, title=title,
                                 action="list_all", url=url))

    elif item.title == "Alfabetico":
        url = '%sletter/0-9/' % host
        itemlist.append(Item(channel=item.channel, title='#',
                             action="alpha_list", url=url))

        for l in string.ascii_uppercase:
            url = '%sletter/%s/' % (host, l.lower())
            title = l
            itemlist.append(Item(channel=item.channel, title=title,
                                 action="alpha_list", url=url))

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
            continue
            # new_item.contentSerieName = title
            # new_item.action = "seasons"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        next_page = data.find("a", class_="next page-numbers")["href"]
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist


# def seasons(item):
#     logger.info()

#     itemlist = list()

#     soup = create_soup(item.url).find_all("div", class_="Wdgt AABox")

#     infoLabels = item.infoLabels
#     if len(soup) == 1:
#         item.infoLabels["season"] = 1
#         item.action = 'episodesxseason'
#         return episodesxseason(item)
#     for elem in soup:
#         season = elem.find("div", class_="AA-Season")["data-tab"]
#         title = "Temporada %s" % season
#         infoLabels["season"] = season
#         itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseason',
#                              infoLabels=infoLabels))

#     tmdb.set_infoLabels_itemlist(itemlist, True)

#     if config.get_videolibrary_support() and len(itemlist) > 0 and not item.extra:
#         itemlist.append(Item(channel=item.channel,
#                              title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
#                              url=item.url,
#                              action="add_serie_to_library",
#                              extra="episodios",
#                              contentSerieName=item.contentSerieName
#                              ))

#     return itemlist


# def episodios(item):
#     logger.info()

#     itemlist = list()
#     templist = seasons(item)
#     for tempitem in templist:
#         itemlist += episodesxseason(tempitem)

#     return itemlist


# def episodesxseason(item):
#     logger.info()

#     itemlist = list()

#     soup = create_soup(item.url).find_all("div", class_="Wdgt AABox")
#     infoLabels = item.infoLabels
#     season = infoLabels["season"]

#     for elem in soup:
#         if elem.find("div", class_="AA-Season")["data-tab"] == str(season):
#             epi_list = elem.find_all("tr")
#             for epi in epi_list:
#                 url = epi.a["href"]
#                 epi_num = epi.find("span", class_="Num").text
#                 epi_name = epi.find("td", class_="MvTbTtl").a.text
#                 infoLabels["episode"] = epi_num
#                 title = "%sx%s - %s" % (season, epi_num, epi_name)

#                 itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
#                                      infoLabels=infoLabels))
#             break
#     tmdb.set_infoLabels_itemlist(itemlist, True)

#     if config.get_videolibrary_support() and len(itemlist) > 0 and not item.extra and season == 1:
#         itemlist.append(Item(channel=item.channel,
#                              title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
#                              url=item.url,
#                              action="add_serie_to_library",
#                              extra="episodios",
#                              contentSerieName=item.contentSerieName
#                              ))

#     return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|#038;|\(.*?\)|\s{2}|&nbsp;", "", data)
    data = scrapertools.decodeHtmlentities(data)
    
    patron = r'data-tplayernv="Opt(\d+)"><span.*?<span>(\w+)\s*-\s*([^<]+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, lang, quality in matches:
        language = IDIOMAS.get(lang, lang)
        patron = '<iframe width="560" height="315" src="([^"]+)"'
        
        url_tr = scrapertools.find_single_match(data, 'id="Opt%s">%s' % (option, patron))
        new_data = httptools.downloadpage(url_tr).data
        
        url_embed = scrapertools.find_single_match(new_data, patron)
        data_embed = httptools.downloadpage(url_embed).data

        patron1 = r"addiframe\('([^']+)'"
        match1 = re.compile(patron1, re.DOTALL).findall(data_embed)
        
        for url in match1:
            itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play',
                            infoLabels=item.infoLabels, language=language, quality=quality))
    
    #downlist = get_downlist(item, data)
    #itemlist.extend(downlist)
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server)
    itemlist = sorted(itemlist, key=lambda i: i.language)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist




def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        if texto != '':
            item.url += texto
            return list_all(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def fix_title(title):
    title = re.sub(r'\((.*)', '', title)
    title = re.sub(r'\[(.*?)\]', '', title)
    return title

