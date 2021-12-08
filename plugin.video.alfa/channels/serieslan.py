# -*- coding: utf-8 -*-

from builtins import range
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib                                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                                               # Usamos el nativo de PY2 que es más rápido

import re
import string
import json

from channels import renumbertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import filtertools
from channels import autoplay
from lib import gktools

IDIOMAS = {'latino': 'Latino'}
list_language = list(IDIOMAS.values())
list_servers = []
list_quality = ['default']


host = "https://serieslan.com"

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

def mainlist(item):
    logger.info()
    thumb_series = get_thumb("tvshows", auto=True)
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Novedades",
            url=host, thumbnail=thumb_series, category="series",
            page=0, plot="Tus series animadas de la infancia"))

    itemlist.append(
        Item(channel=item.channel, action="letters", title="Listado alfabético",
            url=host+"/lista.php?or=abc", thumbnail=get_thumb("alphabet", auto=True), page=0,
            plot="Tus series animadas de la infancia"))

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Series Live Action",
            url=host+"/liveaction", thumbnail=thumb_series, page=0, category="liveaction",
            plot="Series LiveAction de los 90s y 2000"))
    
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
            thumbnail=get_thumb("search", auto=True)))

    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def letters(item):
    logger.info()
    itemlist = []
    
    itemlist.append(
        Item(channel=item.channel, action="list_all", title="0-9", character = "0",
            url=item.url, thumbnail=item.thumbnail, page=0))

    for letter in list(string.ascii_lowercase):
        itemlist.append(item.clone(action="list_all", title=letter.upper(), character = letter,
        url=item.url))

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host +"/b.php"
    item.texto = texto
    if texto != '':
        return sub_search(item)
    else:
        return []

def sub_search(item):
    logger.info()
    itemlist = []
    logger.info(item.url)
    post = "k=" + item.texto
    logger.info(post)
    results = httptools.downloadpage(item.url, post=post).data#.json
    results = json.loads(results)
    if not results:
        return itemlist
    for result in results["dt"]:
        scrapedthumbnail = "{}/tb/{}.jpg".format(host,result[0])
        scrapedtitle = result[1]
        scrapedurl = host + "/" + result[2]

        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        try:
            scrapedyear = result[3]
        except:
            scrapedyear = ''
        filtro_tmdb = list({"first_air_date": scrapedyear}.items())
        itemlist.append(item.clone(action = "seasons",
                                   title = scrapedtitle,
                                   thumbnail = scrapedthumbnail,
                                   url = scrapedurl,
                                   context=context,
                                   contentSerieName = scrapedtitle,
                                   page=0,
                                   infoLabels={'filtro':filtro_tmdb}
                        ))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist

def lista(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    classitems = "link" if item.category == "series" else "min-la"
    matches = soup.find_all("a", class_= classitems )
    
    next_page = soup.find("a", class_="sa fr")
    num_items_x_pagina = 25
    min = item.page
    max = item.page + num_items_x_pagina
    f_page = item.page + num_items_x_pagina

    for elem in matches[min:max]:
        scrapedurl = elem["href"]
        scrapedthumbnail = elem.find("img")["src"]
        scrapedtitle = elem.find("h3").text if item.category == "series" else elem.find("div").text
        
        title = scrapedtitle.replace(" y "," & ") if " y " in scrapedtitle else scrapedtitle
        url = host + scrapedurl
        thumbnail = host + scrapedthumbnail

        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)

        itemlist.append(Item(channel=item.channel, title=title, url=url,
            action="seasons", thumbnail=thumbnail, contentSerieName=title, context=context))

    if f_page < len(matches):
        itemlist.append(item.clone(title="[COLOR cyan]Página Siguiente >>[/COLOR]", page=f_page))

    elif next_page:
        next_page = "{}/{}".format(host, next_page) 
        itemlist.append(
            Item(channel=item.channel, url=next_page, action="lista",
                title="[COLOR cyan]Página Siguiente >>[/COLOR]",
                page=0, tipo=item.tipo))

    tmdb.set_infoLabels(itemlist)
    return itemlist

def list_all(item):
    logger.info()
    itemlist = []

    soup = create_soup(item.url)
    letter = [str(d) for d in range(10)] + ['¡'] + ['¿'] if item.character == '0' else item.character.lower()
    
    matches = soup.find_all("div", class_="el")

    for elem in matches:
        if elem.find("h2").text[0].lower() in letter:
            scrapedtitle = elem.find("h2").text
            scrapedthumbnail = elem.find("img")['data-original']
            scrapedurl = elem.find("a")["href"]
            
            title = scrapedtitle.replace(" y "," & ") if " y " in scrapedtitle else scrapedtitle
            url = host + "/" + scrapedurl
            thumbnail = host + scrapedthumbnail
            
            context = renumbertools.context(item)
            context2 = autoplay.context
            context.extend(context2)
            
            itemlist.append(Item(channel=item.channel, title=title, url=url,
                action="seasons", thumbnail=thumbnail, contentSerieName=title, context=context))
    
    #if f_page < len(matches) and len(itemlist)>30:
    #    itemlist.append(item.clone(title="[COLOR cyan]Página Siguiente >>[/COLOR]", page=f_page))

    return itemlist

def seasons(item, add_to_videolibrary = False):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    match = soup.find("div", class_="box lista")
    matches = match.find_all("h3", class_="colapse")
    infoLabels = item.infoLabels
    for i, elem in enumerate(matches):
        title = elem.text
        dt = elem['dt']
        season = 1 if "unica" in title.lower() else title.split(" ")[1] if "temporada" in title.lower() else 0
        if not "temporada" in title.lower():
            season = i+1 if not [int(s) for s in title if s.isdigit()] else [int(s) for s in title if s.isdigit()][0]
        infoLabels['season'] = season
        itemlist.append(Item(channel=item.channel, title=title, contentSerieName=item.tile,
                url=item.url, plot=item.plot, thumbnail=item.thumbnail, dt = dt,
                action="episodesxseason", context=item.context, infoLabels=infoLabels))
    if config.get_videolibrary_support() and len(itemlist) > 0 and add_to_videolibrary == False:
        itemlist.append(Item(channel=item.channel, url=item.url, action="add_serie_to_library",
                        extra="episodios", contentSerieName=item.contentSerieName,
                        title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]'))
    return itemlist

def episodesxseason(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    episodes = soup.find("div", {"id": item.dt})

    total_episode = 0

    infoLabels = item.infoLabels
    for episode in episodes.find_all("a"):
        scrapedurl = "/"+episode["href"]
        scrapedtitle = episode.find("li").text
        infoLabels['episode'] = scrapedtitle.split(" -")[0].split(" ")[1]

        pat = "/" if not "KND" in item.title else "-"
        name = scrapedtitle.split(" -")[1]
        
        title = ''
        if len(name.split(pat)) > 1:
            for j, pos in enumerate(name.split(pat)):
                total_episode += 1
                season, episode_numb = renumbertools.numbered_for_tratk(item.channel, 
                    item.contentSerieName, infoLabels['season'], total_episode)
                if len(name.split(pat)) == j+1:
                    title += "{}x{:02d}".format(season, episode_numb)
                else:
                    title += "{}x{:02d}_".format(season, episode_numb)
        else:
            total_episode += 1
            season, episode_numb = renumbertools.numbered_for_tratk(item.channel,
                item.contentSerieName, infoLabels['season'], total_episode)
            title += "{}x{:02d}".format(season, episode_numb)
        title = "{} - {}".format(title,scrapedtitle.split(" -")[1])

        itemlist.append(Item(channel=item.channel, title=title, contentSerieName=item.title,
                url=host + scrapedurl, plot=item.plot, thumbnail=item.thumbnail,
                action="findvideos", context=item.context, infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist

def episodios(item):
    logger.info()
    itemlist = list()
    templist = seasons(item, add_to_videolibrary = True)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    _sa = scrapertools.find_single_match(data, 'var _sa = (true|false);')
    _sl = scrapertools.find_single_match(data, 'var _sl = ([^;]+);')
    sl = eval(_sl)
    buttons = scrapertools.find_multiple_matches(data, '<button.*?class="selop" sl="([^"]+)">')
    if not buttons:
        buttons = [0,1,2]
    for id in buttons:
        title = '%s'
        new_url = golink(int(id), _sa, sl)
        data_new = httptools.downloadpage(new_url).data
        matches = scrapertools.find_multiple_matches(data_new, 'javascript">(.*?)</script>')
        js = ""
        for part in matches:
            js += part
        #logger.info("test before:" + js)

        try: 
            matches = scrapertools.find_multiple_matches(data_new, '" id="(.*?)" val="(.*?)"')
            for zanga, val in matches:
                js = js.replace('var %s = document.getElementById("%s");' % (zanga, zanga), "")
                js = js.replace('%s.getAttribute("val")' % zanga, '"%s"' % val)
            #logger.info("test1 after:" +js)
        except:
            pass
        
        #v1
        js = re.sub('(document\[.*?)=', 'prem=', js)
        
        #Parcheando a lo bruto v2
        video = scrapertools.find_single_match(js, "sources: \[\{src:(.*?), type")
        js = re.sub(' videojs\((.*?)\);', video+";", js)
        
        from lib import js2py
        js2py.disable_pyimport()
        context = js2py.EvalJs({'atob': atob})
        
        try:
            result = context.eval(js)
        except:
            logger.error("Js2Py no puede desofuscar el codigo, ¿cambió?")
            continue

        url = scrapertools.find_single_match(result, 'src="(.*?)"')
        #v2
        if not url:
            url = result.strip()
        
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='play', language='latino',
                         infoLabels=item.infoLabels))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist

def golink (num, sa, sl):
    b = [3, 10, 5, 22, 31]
    #d = ''
    #for i in range(len(b)):
    #    d += sl[2][b[i]+num:b[i]+num+1]

    SVR = "https://viteca.stream" if sa == 'true' else "http://serieslan.com"
    TT = "/" + urllib.quote_plus(sl[3].replace("/", "><")) if num == 0 else ""
    url_end = link(num,sl)
    #return SVR + "/el/" + sl[0] + "/" + sl[1] + "/" + str(num) + "/" + sl[2] + d + TT
    return SVR + "/el/" + sl[0] + "/" + sl[1] + "/" + str(num) + "/" + sl[2] + url_end + TT

def link(ida,sl):
    a=ida
    b=[3,10,5,22,31]
    c=1
    d=""
    e=sl[2]
    for i in range(len(b)):
      d=d+substr(e,b[i]+a,c)
    return d

def substr(st,a,b):
    return st[a:a+b]
'''
def x92(data1, data2):
    data3 = []
    data4 = 0
    data5 = ""
    data6 = ""
    for i in range(len(256)):
      data3[i] = i
    for i in range(len(256)):
      data4 = (data4 + data3[i] + ord(data1[i])) % 256
      data5 = data3[i]
      data3[i] = data3[data4]
      data3[data4] = data5
    i = 0
    data4 = 0
    for j in range(len(data2)):
        i = (i + 1) % 256
        data4 = (data4 + data3[i]) % 256
        data5 = data3[i]
        data3[i] = data3[data4]
        data3[data4] = data5
        data6 =1#+= str(unichr(data2[ord(str(j)) ^ data3[(data3[i] + data3[data4]) % 256]))
    return data6

def _ieshlgagkP(umZFJ):
    return umZFJ
def _RyHChsfwdd(ZBKux):
    return ZBKux
def _eladjkKtjf(czuwk):
    return czuwk
def _slSekoKrHb():
    return ''
def _VySdeBApGO():
    return 'Z'

def _nEgqhkiRub():
    return 28

def _lTjZxWGNnE():
    return 57
'''
def atob(s):
    import base64
    return base64.b64decode(s.to_string().value)
