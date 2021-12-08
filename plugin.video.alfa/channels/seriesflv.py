# -*- coding: utf-8 -*-
# -*- Channel SeriesFLV -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
import sys
import base64

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from channels import filtertools
from bs4 import BeautifulSoup
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from channels import autoplay
from platformcode import config, logger
from lib.AlfaChannelHelper import DooPlay
from channelselector import get_thumb

host = 'https://seriesflv.xyz/'
AlfaChannel = DooPlay(host, tv_path="/online-series-completas")

IDIOMAS = {'esp': 'CAST', 'lat': 'LAT', 'sub': 'VOSE', "ing": 'VO'}
list_idiomas = list(IDIOMAS.values())
list_servers = ['fembed', 'streamtape', 'cloudvideo', 'mixdrop']
list_quality = []


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Nuevos Capítulos", action="novedades", url=host + "ver",
                         thumbnail=get_thumb("new episodes", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Ultimas series", action="list_all",
                         url=host + "online-series-completas",
                         thumbnail=get_thumb("last", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=host + "online-series-completas",
                         thumbnail=get_thumb("genres", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por Año", action="section", url=host + "online-series-completas",
                         thumbnail=get_thumb("year", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "?s=",
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_idiomas, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item)


def section(item):
    logger.info()

    item.url = "%s%s" % (host, "online-series-completas")

    if item.title == "Generos":
        return AlfaChannel.section(item, section="genre")
    else:
        return AlfaChannel.section(item, section="year")


def seasons(item):
    logger.info()

    itemlist = list()
    data = AlfaChannel.create_soup(item.url).find_all("script")[-2]
    al = scrapertools.find_single_match(data["src"], 'base64,(.*)')
    fa = base64.b64decode(al)
    id = scrapertools.find_single_match(fa, 'var id=(\d+)')
    post = {"action": "seasons", "id": id}
    soup = AlfaChannel.get_data_by_post(post=post).soup
    matches = soup.find_all("span", class_="se-t")
    infoLabels = item.infoLabels

    for elem in matches:
        season = elem.text
        title = "Temporada %s" % season
        infoLabels["season"] = season

        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseason',
                             context=filtertools.context(item, list_idiomas, list_quality), infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = list()

    data = AlfaChannel.create_soup(item.url).find_all("script")[-2]
    al = scrapertools.find_single_match(data["src"], 'base64,(.*)')
    fa = base64.b64decode(al)
    id = scrapertools.find_single_match(fa, 'var id=(\d+)')

    post = {"action": "seasons", "id": id}
    try:
        itemlist = AlfaChannel.episodes(item, post=post, postprocess=get_lang)

        itemlist = filtertools.get_links(itemlist, item, list_idiomas)
    except:
        pass

    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()
    templist = seasons(item)

    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def novedades(item):
    logger.info()

    itemlist = list()

    soup = AlfaChannel.create_soup(item.url).find("div", id="archive-content")

    for elem in soup.find_all("article"):
        languages = list()
        title = elem.find("span", class_="serie").text
        c_title = scrapertools.find_single_match(title, "([^\(]+)").strip()
        lang_data = elem.find_all("img")
        url = elem.a["href"]
        thumb = lang_data[0].get("src", "")
        for l_data in lang_data[1:]:
            languages.append(IDIOMAS.get(l_data.get("title", "sub")[:3].lower(), "VOSE"))
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos", thumbnail=thumb,
                             contentSerieName=c_title, language=languages, infoLables={}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup, matches = AlfaChannel.get_video_options(item.url)

    for lang_data in matches:
        lang = lang_data.find("span", class_="title").text[:3].lower()
        data_tab = lang_data.get("data-tab", "")
        post_data = soup.find("div", id=data_tab).find_all("li")
        for elem in post_data:
            srv = elem.find("span", class_="title").text.lower()
            post = {"action": "doo_player_ajax", "post": elem["data-post"], "nume": elem["data-nume"],
                    "type": elem["data-type"]}

            itemlist.append(Item(channel=item.channel, title="%s", action="play", post=post, ref=item.url, server=srv,
                                 language=IDIOMAS.get(lang, "VOSE"), infoLabels=item.infoLabels))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_idiomas)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    if item.contentType != "episode":
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != "findvideos":
            itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]",
                                 url=item.url, action="add_pelicula_to_library", extra="findvideos",
                                 contentTitle=item.contentTitle))

    return itemlist


def play(item):
    logger.info()

    itemlist = list()

    doo_url = "%swp-admin/admin-ajax.php" % host
    data = httptools.downloadpage(doo_url, post=item.post, headers={"referer": item.ref}).data
    try:
        url = BeautifulSoup(data, "html5lib").find("iframe")["src"]
    except:
        return

    if not url.startswith("http"):
        url = "https:%s" % url

    itemlist.append(item.clone(url=url, server=''))

    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.first = 0
        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def get_lang(*args):

    langs = list()

    try:
        lang_list = args[1].find("div", class_="lang_ep").find_all("img")
        for lang in lang_list:
            langs.append(lang.get("title", "subtitulado")[:3].lower())
    except:
       langs = ""

    args[2].language = langs
    return args[2]
