# -*- coding: utf-8 -*-
# -*- Channel Xdede -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
from builtins import range
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger

#unify = config.get_setting('unify')

IDIOMAS = {'1':'CAST', '2':'LAT', '3':'VOSE', '4':'VO'}
list_language = list(IDIOMAS.values())

list_quality = ['Oficial', '1080p', '720p', '480p', '360p']

list_servers = ['fembed', 'vidcloud','clipwatching', 'gamovideo']

host = 'https://movidy.co/'
host2 = 'https://wmovies.co/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu', type='peliculas',
                         thumbnail= get_thumb('movies', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Series', action='sub_menu', type='series',
                         thumbnail= get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Animes', action='sub_menu', type='animes',
                         thumbnail= get_thumb('anime', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Colecciones', action='list_collections',
                        url= host+'listas', thumbnail=get_thumb('colections', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Buscar...', action="search",
                         url=host + 'search?go=', thumbnail=get_thumb("search", auto=True)))

    itemlist.append(Item(channel=item.channel,
                             title="Configurar Canal...",
                             text_color="turquoise",
                             action="settingCanal",
                             thumbnail=get_thumb('setting_0.png'),
                             url='',
                             fanart=get_thumb('setting_0.png')
                             ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def sub_menu(item):
    logger.info()

    itemlist=[]

    url_estreno = host + item.type + '/novedades'
    
    if item.type == 'peliculas':
        url_estreno = host + item.type + '/estrenos'
        itemlist.append(Item(channel=item.channel, title='Estrenos', url=url_estreno, action='list_all',
                         thumbnail=get_thumb('estrenos', auto=True), type=item.type))
    else:
        itemlist.append(Item(channel=item.channel, title='Nuevos Capitulos', url=url_estreno, action='list_all',
                         thumbnail=get_thumb('new episodes', auto=True), type=item.type))

    itemlist.append(Item(channel=item.channel, title='Novedades', url=host+item.type, action='list_all',
                         thumbnail=get_thumb('newest', auto=True), type=item.type))
    
    itemlist.append(Item(channel=item.channel, title='Actualizadas', url=host+'/actualizado/'+item.type,
                         action='list_all', thumbnail=get_thumb('updated', auto=True), type=item.type))
    
    itemlist.append(Item(channel=item.channel, title='Mejor Valoradas', url=host+item.type+'/mejor-valoradas',
                         action='list_all', thumbnail=get_thumb('more voted', auto=True), type=item.type))
    
    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True), type=item.type))
    
    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True), type=item.type))

    return itemlist

def settingCanal(item):
    from platformcode import platformtools
    platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def section(item):
    logger.info()
    itemlist=[]
    if 'Genero' in item.title:
        list_genre = {"Acción","Animación","Bélica","Ciencia ficción",
                      "Comedia","Crimen","Drama","Familia","Misterio",
                      "Música","Romance","Suspense","Terror","Wester"}
        for name in list_genre:
            url = '%s%s/filtro/%s,/,' % (host, item.type, name)
            
            itemlist.append(Item(channel=item.channel, url=url, title=name,
                                 action='list_all', type=item.type))
    else:
        try:
            import datetime
            now = datetime.datetime.now()
            c_year = now.year + 1
        except:
            c_year = 2020
        l_year = c_year - 19
        year_list = list(range(l_year, c_year))

        for year in year_list:
            year = str(year)
            url = '%s%s/filtro/,/%s,' % (host, item.type, year)
            
            itemlist.append(Item(channel=item.channel, title=year, url=url,
                                 action="list_all", type=item.type))
        itemlist.reverse()
        itemlist.append(Item(channel=item.channel, title='Introduzca otro año...', url='',
                                 action="year_cus", type=item.type))

    return itemlist

def year_cus(item):
    from platformcode import platformtools
    heading = 'Introduzca Año (4 digitos)'
    year = platformtools.dialog_numeric(0, heading, default="")
    item.url = '%s%s/filtro/,/%s,' % (host, item.type, year)
    item.action = "list_all"
    if year and len(year) == 4:
        return list_all(item)

def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<article class="Cards.*?href="([^"]+)"(.*?)<img.*?'
    patron += 'data-echo="([^"]+)" alt="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedinfo, scrapedthumbnail, scrapedtitle in matches:

        title = scrapedtitle
        scrapedtitle = re.sub(r' \((.*?)\)$', '', scrapedtitle)
        thumbnail = scrapedthumbnail.strip()
        url = scrapedurl
        tmdb_id = scrapertools.find_single_match(url, r'/\w(\d+)-')
        

        thumbnail = re.sub(r'p/w\d+', 'p/original', thumbnail)
        
        # if item.type == 'search':
        #     s_title =  scrapertools.find_single_match(url, host+'(\w+)')
        #     if not unify:
        #         title += ' [COLOR grey][I](%s)[/I][/COLOR]' % s_title.capitalize()[:-1]
        
        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        thumbnail=thumbnail,
                        infoLabels={'tmdb_id':tmdb_id})

        if item.type == 'peliculas' or 'peliculas' in url:
            new_item.action = 'findvideos'
            new_item.contentTitle = scrapedtitle
            new_item.type = 1
            
            calidad_baja = scrapertools.find_single_match(scrapedinfo, r'>(\w+\s\w+)</div>$')
            
            if calidad_baja:
                new_item.quality = 'Baja'
        else:
            new_item.action = 'seasons'
            new_item.contentSerieName = scrapedtitle
            new_item.type = 0
            
            sesxep = scrapertools.find_single_match(url, r'/(\d+x\d+)$')
            
            if sesxep:
                new_item.title += ' '+sesxep
                new_item.action = 'findvideos'
            

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    if item.type == 'search':
        itemlist.sort (key=lambda i: (i.type, i.title))
    #  Paginación

    url_next_page = scrapertools.find_single_match(data,'<a href="([^"]+)" up-target="body">Pagina s')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all', text_color='gold'))

    return itemlist

def list_collections(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<article>(.*?)href="([^"]+)".*?<h2>([^<]+)</h2><p>([^<]+)</p>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for thumb, url, title, plot in matches:
        thumbnail = scrapertools.find_single_match(thumb, '<img src="([^"]+)">')
        if thumbnail:
            thumb = re.sub('p/w\d+', 'p/original', thumbnail)
        else:
            thumb = 'https://i.imgur.com/P4g4aW2.png'

        itemlist.append(Item(channel=item.channel, action='list_all', title=title, url=url, thumbnail=thumb, plot=plot))

    url_next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)"')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_collections'))
    return itemlist


def seasons(item):
    logger.info()

    itemlist=[]

    data = get_source(item.url)
    patron = "activeSeason\(this,'temporada-(\d+)'"
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for season in matches:
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

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

    itemlist = []
    infoLabels = item.infoLabels

    data=get_source(item.url)
    
    pat = '<div class="season temporada-%s(.*?)</a></li></div>' % item.infoLabels['season']
    data = scrapertools.find_single_match(data, pat)
    
    patron= '<li ><a href="([^"]+)"(.*?)'
    patron += r'<h2>([^>]+)</h2>.*?<span>\d+ - (\d+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, sthumbnail, scrapedtitle, ep in matches:
        thumbnail = scrapertools.find_single_match(sthumbnail, 'data-echo="([^"]+)"')
        thumb = re.sub(r'p/w\d+', 'p/original', thumbnail)
        infoLabels['episode'] = ep
        
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             infoLabels=infoLabels, thumbnail=thumb))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []
    itemlist2 = []
    headers = {'Referer': item.url}
    users_links = config.get_setting('show_users_links', 'movidy')

    server_l = {'waaw': 'netu', 'powvldeo': 'powvideo', 'beta': 'directo'
                  }

    data = get_source(item.url)
    ref_ = scrapertools.find_single_match(data, r'<iframe src="(https://wmovies.co/ifr/\w\d+)"')
    s_id = scrapertools.find_single_match(ref_, 'ifr/(\w\d+)')
    
    if s_id:
        import requests
        url = host2+"cpt"
        header = {'Referer': ref_}
        session = requests.Session()
        page = session.post(url, data={'type': '1', 'id': s_id}, headers=header).json()
        
        if page.get('status', 0) == 200:
            
            data2 = page['data']
            data2 = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data2)
            
            patron = r'<div class="OD_(\d+)(.*?)</div>'
            patron1 = r"onclick=\"go_to_player\('([^']+)'.*?<span>([^<]+)"
            matches = re.compile(patron, re.DOTALL).findall(data2)
           
            for language, info in matches:
                
                lang = IDIOMAS.get(language, 'VO')
                matches1 = re.compile(patron1, re.DOTALL).findall(info)
                
                for url, serv in matches1:

                    if 'google' in serv.lower():
                        continue
                    
                    url = host2+url


                    quality = 'Oficial'

                    title = '%s [%s]' % (serv.capitalize(), lang)
                    serv = server_l.get(serv.lower(), serv.lower())
                    p_quality = -2000

                    itemlist.append(Item(channel=item.channel, title=title, url=url, action='play', language=lang,
                                     quality=quality, headers=header, infoLabels=item.infoLabels,
                                     p_lang=language, p_quality=p_quality, server=serv))
    
    if users_links == 0:
        
        data = scrapertools.find_single_match(data, '<div class="linksUsers">(.*?)</html>')
        patron = '<li><a href="([^"]+)".*?<img.*?>([^<]+)<b>([^<]+)<.*?src="([^"]+)"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        
        for url, server, quality, language in matches:

            if '/sc_' in url:
                continue
            if url != '':
        
                try:
                    server = server.split(".")[0].replace('1', 'l')
                except:
                    continue
        
                # _id = scrapertools.find_single_match(url, r'link/\w+(.*)')
        
                server = server_l.get(server.lower(), server)
        
                # if not url.startswith(host):
                #     url = url % _id
        
                language = scrapertools.find_single_match(language, r'/(\d+)\.png')
                lang = IDIOMAS.get(language, 'VO')
        
                title = '%s [%s] [%s]' % (server.capitalize(), lang, quality)
                
                try:
                    p_quality = -int(quality.replace('p', ''))
                except:
                    p_quality = 0
        
                itemlist2.append(Item(channel=item.channel, title=title, url=url, action='play', language=lang,
                                     quality=quality, server=server.lower(), headers=headers, infoLabels=item.infoLabels,
                                     p_lang=language, p_quality=p_quality, _type="user"))

        

        
        itemlist.extend(itemlist2)
    
    itemlist.sort(key=lambda i: (i.p_lang, i.p_quality, i.server))

    # if not itemlist:
    #     itemlist.append(Item(channel=item.channel, folder=False, text_color='tomato',
    #                         title='[I] Aún no hay enlaces disponibles [/I]'))
    #     return itemlist
    
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    
    if not item.url.startswith(host2):
        return item
    
    url = item.url
    header = item.headers
    item.server = ''
    if item._type == 'user':
        req = httptools.downloadpage(url, headers=header).data
        url = scrapertools.find_single_match(req, 'Go_V2" href="([^"]+)"')
    else:
        
        if 'procesador-servidores' in url:
            req = httptools.downloadpage(url, headers=header).json
            data = req.get("data")
            if req.get('total'):
                data = req.get("data").get("data")
                if 'beta' in item.title.lower():
                    item.server = 'directo'
            url = "%sget-player/%s" % (host2, data)
        req = httptools.downloadpage(url, headers=header, follow_redirects=False)
        location = req.headers.get('location', None)

        if location:
            url = location
        else:
            new_data = req.data.replace("'", '"')
            url = scrapertools.find_single_match(new_data, 'file": "([^"]+)"')
    
    if url:
          item.url = url.replace("isthebest.rest", ".com")

    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)
    
    return itemlist




def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.type = 'search'
    if texto != '':
        try:
            return list_all(item)
        except:
            import sys
            for line in sys.exc_info():
                logger.error("{0}".format(line))
            return []
    else:
        return []

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'peliculas'
        elif categoria == 'infantiles':
            item.url = host + 'peliculas/filtro/Animación,/,'
        elif categoria == 'terror':
            item.url = host + 'peliculas/filtro/Terror,/,'
        item.type='peliculas'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
