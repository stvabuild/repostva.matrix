# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import codecs

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channels import filtertools, autoplay
from platformcode import config, logger
from channelselector import get_thumb
from bs4 import BeautifulSoup

host = 'https://www.ultrapeliculashd.com'
forced_proxy_opt = 'ProxyDirect'


IDIOMAS = {'mx': 'LAT', 'es': 'CAST', 'en':'VOSE'}
list_language = list(IDIOMAS.values())
list_quality = ['default', '1080p', 'HD', 'CAM']
list_servers = ['fembed', 'uqload']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Estrenos",
                         action="list_all",
                         thumbnail=get_thumb('premieres', auto=True),
                         url=host + '/genre/estrenos-ultra-hd/', first=0
                         ))

    itemlist.append(Item(channel=item.channel, title="Actualizadas",
                         action="list_all",
                         thumbnail=get_thumb('updated', auto=True),
                         url=host + '/pelicula/', first=0
                         ))

    itemlist.append(Item(channel=item.channel, title="Destacadas",
                         action="list_all",
                         thumbnail=get_thumb('hot', auto=True),
                         url=host + '/genre/destacados/', first=0
                         ))

    itemlist.append(Item(channel=item.channel, title="Generos",
                         action="generos",
                         url=host,
                         thumbnail=get_thumb('genres', auto=True)
                         ))

    itemlist.append(Item(channel=item.channel, title="Alfabetico",
                         action="section",
                         url=host,
                         thumbnail=get_thumb('alphabet', auto=True),
                         extra='alfabetico'
                         ))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                         action="search",
                         url=host + '/?s=',
                         thumbnail=get_thumb('search', auto=True)
                         ))

    autoplay.show_option(item.channel, itemlist)

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


def list_all(item):
    logger.info()

    itemlist = list()
    next = False

    soup = create_soup(item.url)

    matches = soup.find("div", class_="items").find_all("article", id=re.compile(r"^post-\d+"))

    first = item.first
    last = first + 20
    if last >= len(matches):
        last = len(matches)
        next = True

    for elem in matches[first:last]:

        info_1 = elem.find("div", class_="poster")
        info_2 = elem.find("div", class_="data")

        thumb = info_1.img["src"]
        title = info_1.img["alt"]
        url = info_1.a["href"]
        year = info_2.find("span", text=re.compile(r"\d{4}")).text.strip()
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             thumbnail=thumb, contentTitle=title, infoLabels={'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if not next:
        url_next_page = item.url
        first = last
    else:
        #try:
        url_next_page = soup.find("a", class_="arrow_pag")["href"]
        # except:
        #     return itemlist

        url_next_page = '%s' % url_next_page
        first = 0

    if url_next_page and len(matches) > 20:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all',
                             first=first))

    return itemlist


def generos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    matches = soup.find("ul", class_="sub-menu")

    for elem in matches:

        title = elem.a.text.capitalize()
        url = elem.a["href"]

        itemlist.append(Item(channel=item.channel, url=url, title=title, action="list_all", first=0))

    return itemlist


def section(item):
    logger.info()
    itemlist = list()

    soup = create_soup(host)

    matches = soup.find("ul", class_="glossary")

    for elem in matches:
        title = elem.a.text
        itemlist.append(Item(channel=item.channel, action="alpha", title=title.upper()))
    return itemlist


def alpha(item):
    logger.info()

    itemlist = []

    url = '%s/wp-json/dooplay/glossary/?term=%s&nonce=4e850b7d59&type=all' % (host, item.title.lower())
    dict_data = httptools.downloadpage(url, forced_proxy_opt=forced_proxy_opt).json
    if 'error' not in dict_data:
        for elem in dict_data:
            elem = dict_data[elem]
            thumb = re.sub(r'-\d+x\d+.jpg', '.jpg', elem['img'])
            try:
                year = elem["year"]
            except:
                year = '-'
            itemlist.append(Item(channel=item.channel, action='findvideos', title=elem['title'],
                                 url=elem['url'], thumbnail=thumb, contentTitle=elem['title'],
                                 infoLabels={"year": year}))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url, unescape=True)

    sources = soup.find("div", class_="playex")
    langs = soup.find("ul", class_="idTabs sourceslist")

    for elem in sources.find_all("div", class_="play-box-iframe"):

        opt = elem["id"]
        url = elem.iframe["src"]
        if "hideload" in url:
            url = unhideload(url)

        lang_data = langs.find("a", href=re.compile(r"^#%s" % opt))
        if lang_data:
            lang = languages_from_flags(lang_data.span, "png")
        else:
            lang = ''
        itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url,
                             language=lang, infoLabels=item.infoLabels))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def unhideload(url):
    logger.info()
    server_dict = {"ud": "https://waaw.tv/watch_video.php?v=",
                   "od": "https://www.fembed.com/v/",
                   "ad": "https://uqload.com/embed-",
                   "id": "https://waaw.tv/f/",
                   "bd": "https://gounlimited.to/embed-"}

    server = server_dict[scrapertools.find_single_match(url, "(\wd)=")]

    hash_ = url.split("=")[1].split("&")[0]
    inv = hash_[::-1]
    result = codecs.decode(inv, "hex").decode("utf-8")
    url = "%s%s" % (server, result)
    return url


def languages_from_flags(lang_data, ext):
    logger.info()
    language = []
    lang_list = lang_data.find_all("img")
    for lang in lang_list:
        lang = scrapertools.find_single_match(lang["src"], "(\w+).%s" % ext)

        language.append(IDIOMAS.get(lang, "VOSE"))
    return language


def search_results(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    for elem in soup.find_all("div", class_="result-item"):

        url = elem.a["href"]
        thumb = elem.img["src"]
        title = elem.img["alt"]
        year = elem.find("span", class_="year").text

        itemlist.append(Item(channel=item.channel, title=title, contentTitle=title, url=url, thumbnail=thumb,
                             action='findvideos', infoLabels={'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.first = 0
    if texto != '':
        return search_results(item)
    else:
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    item.extra = 'estrenos/'
    item.first = 0
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + '/genre/estrenos/'

        elif categoria == 'infantiles':
            item.url = host + '/genre/animacion/'

        elif categoria == 'terror':
            item.url = host + '/genre/terror/'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
