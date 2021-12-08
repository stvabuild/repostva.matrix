# -*- coding: utf-8 -*-
# -*- Channel PelisPop -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from core import tmdb
from core import httptools
from core.item import Item
from core import scrapertools
from core import servertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


IDIOMAS = {'latino': 'LAT', 'subtitulado': 'VOSE'}
list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'streamtape',
    'doodstream',
    'evoload',
    ]

host = 'https://pelispop.com/'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu',
                         thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'serie', action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Documentales', url=host + 'documentales', action='list_all',
                         thumbnail=get_thumb('documentary', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section',
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         thumbnail=get_thumb("search", auto=True)))


    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Ultimas', url=host + '%s-agregadas-recientemente/' % item.title.lower(),
                         action='list_all', thumbnail=get_thumb('all', auto=True)))

    if item.title == "Peliculas":
        itemlist.append(Item(channel=item.channel, title='Estrenos', url=host + 'estrenos-2021/', action='list_all',
                             thumbnail=get_thumb('premieres', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + '%s-catalogo-completo/' % item.title.lower(),
                         action='list_all',
                         thumbnail=get_thumb('all', auto=True)))

    return itemlist


def create_soup(url, post=None, unescape=False):
    logger.info()

    if post:
        data = httptools.downloadpage(url, post=post).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)

    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def section(item):
    logger.info()

    itemlist = list()
    base_url = "%s%s" % (host, "generos/")
    matches = create_soup(base_url).find_all("figure", class_="wpb_wrapper vc_figure")

    for elem in matches:
        url = elem.a["href"]
        title = scrapertools.find_single_match(url, "category/([^/]+)")
        itemlist.append(Item(channel=item.channel, title=title.title(), action="list_all", url=url))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="dt-css-grid").find_all("article")

    for elem in matches:
        url = elem.h3.a["href"]
        title = elem.h3.a.text
        thumb = elem.img["src"]
        year = "-"

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})

        if "serie-" in url:
            new_item.contentSerieName = title
            new_item.action = "seasons"
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find("div", class_="pagination").find("span", class_="current").next_sibling["href"]
    except:
        return itemlist

    if url_next_page and len(matches) > 16:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", class_="vc_tta-panels")
    matches = soup.find_all("div", class_="vc_tta-panel")

    infoLabels = item.infoLabels

    for elem in matches:
        season = elem.span.text[-1]
        title = "Temporada %s" % season
        infoLabels["season"] = season
        season_id = elem["id"]
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             context=filtertools.context(item, list_language, list_quality), season_id=season_id,
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist


def episodesxseasons(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", id=item.season_id)

    matches = soup.find_all("a")
    infoLabels = item.infoLabels
    season = infoLabels["season"]

    for elem in matches[1:]:
        url = elem["href"]
        epi_num, epi_name = elem.text.split(" | ")
        epi_num = epi_num[-1]

        infoLabels["episode"] = epi_num
        title = "%sx%s - %s" % (season, epi_num, epi_name)

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()


    soup = create_soup(item.url)
    matches = soup.find_all("div", class_="vc_row-has-fill")
    if not matches:
        return itemlist

    for elem in matches:
        opts = elem.find_all("div", class_="wpb_column")
        for opt in opts:

            if not opt.find("button", class_="vckit-btn"):
                continue
            if opts.index(opt) == 0:
                if "latino" in opt.span.text.lower():
                    lang = "latino"
                else:
                    lang = opt.span.text.lower()[:-1]
                lang = IDIOMAS.get(lang, "VOSE")

            else:
                enc_url = opt.button["href"]
                if not enc_url:
                    continue
                enc_url = re.sub(r"/p/(\d+).php\?v=", r"/p/redirector.php?server=\1&value=", enc_url)
                try:
                    data = httptools.downloadpage(enc_url, headers={"referer": host}).data
                except:
                   continue
                if "ikta.me" in enc_url:
                    from lib import jsunpack
                    packed = scrapertools.find_single_match(data, '<script type="text/javascript">(eval.*?)</script>')
                    unpacked = jsunpack.unpack(packed)
                    url = scrapertools.find_single_match(unpacked, '"file":"([^"]+)')
                else:
                    url = scrapertools.find_single_match(data, "window.location.href = '([^']+)'")
                if url:
                    itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url,
                                         language=lang, infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.text = texto

        if texto != '':
            return search_results(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def search_results(item):
    logger.info()

    itemlist = list()
    url = "%swp-content/plugins/ajax-search-pro/ajax_search.php" % host
    post = {"action": "ajaxsearchpro_search",
            "aspp": item.text,
            "asid": "1",
            "asp_inst_id": "1_1",
            "options": "current_page_id=9&qtranslate_lang=0&filters_changed=0&filters_initial=1&asp_gen%5B%5D=title&asp_gen%5B%5D=content&asp_gen%5B%5D=excerpt&customset%5B%5D=post"
    }
    matches = create_soup(url, post=post).find_all("div", class_="asp_content")
    for elem in matches:
        url = elem.a["href"]
        thumb = elem.find("div", class_="asp_image asp_lazy")["data-src"]
        title = elem.h3.text.strip()

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb,
                        infoLabels={'year': '-'})

        if "serie-" in url:
            new_item.action = "seasons"
            new_item.contentSerieName = new_item.title
            new_item.context = filtertools.context(item, list_language, list_quality)
        else:
            new_item.action = "findvideos"
            new_item.contentTitle = new_item.title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'estrenos-2021/'
        elif categoria == 'infantiles':
            item.url = host + 'category/animacion/'
        elif categoria == 'terror':
            item.url = host + 'category/terror/'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
