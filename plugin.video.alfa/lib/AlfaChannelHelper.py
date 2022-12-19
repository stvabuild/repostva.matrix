# -*- coding: utf-8 -*-
# -*- Alfa Channel Helper -*-
# -*- Herramientas genericas para canales BS -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse
else:
    import urlparse

import re
import traceback

from core import httptools
from core import scrapertools
from core import tmdb
from core import jsontools
from core.item import Item
from platformcode import config
from platformcode import logger

forced_proxy_def = 'ProxyCF'


class AlfaChannelHelper:

    def __init__(self, host, movie_path="/movies", tv_path="/serie", movie_action="findvideos", 
                 tv_action="seasons", canonical={}, url_replace=[], finds={}):
        self.host = host
        self.movie_path = movie_path
        self.tv_path = tv_path
        self.movie_action = movie_action
        self.tv_action = tv_action
        self.doo_url = "%swp-admin/admin-ajax.php" % host
        self.canonical = canonical
        self.url_replace = url_replace
        self.finds = finds

    def create_soup(self, url, **kwargs):
        """
        :param url: url destino
        :param kwargs: parametros que se usan en donwloadpage
        :return: objeto soup o response sino soup
        """

        if "soup" not in kwargs: kwargs["soup"] = True
        if "add_referer" not in kwargs: kwargs["add_referer"] = True
        if "ignore_response_code" not in kwargs: kwargs["ignore_response_code"] = True
        if "canonical" not in kwargs: kwargs["canonical"] = self.canonical
        
        response = httptools.downloadpage(url, **kwargs)
        if kwargs.get("soup", {}):
            soup = response.soup or {}
        else:
            soup = response
        if response.host:
            self.doo_url = self.doo_url.replace(self.host, response.host)
            self.host = response.host

        return soup

    def list_all(self, item, postprocess=None):
        pass

    def limit_results(self, item, matches, lim_max=20):

        next_page = None
        next_limit = None

        if len(matches) > lim_max and not item.next_limit:
            limit = int(len(matches) / 2)
            next_limit = limit
            next_page = item.url
            matches = matches[:limit]
        elif item.next_limit:
            matches = matches[item.next_limit:]

        return matches, next_limit, next_page

    def section(self, item, menu_id=None, section=None, postprocess=None):
        pass

    def seasons(self, item, action="episodesxseason", postprocess=None):
        pass

    def episodes(self, item, action="findvideos", postprocess=None):
        pass

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def):
        pass

    def define_content_type(self, new_item, is_tvshow=False):

        if new_item.infoLabels.get("year", '') and str(new_item.infoLabels["year"]) in new_item.title and len(new_item.title) > 4:
            new_item.title = re.sub("\(|\)|%s" % str(new_item.infoLabels["year"]), "", new_item.title)

        if new_item.contentType == 'episode': 
            new_item.contentSerieName = re.sub('\s*\d+x\d+\s*', '', new_item.title)
            new_item.action = self.movie_action
        elif not is_tvshow and (self.movie_path in new_item.url or not self.tv_path in new_item.url):
            new_item.action = self.movie_action
            new_item.contentTitle = new_item.title
            if not new_item.contentType: new_item.contentType = 'movie'
            if not new_item.infoLabels.get("year", ''):
                new_item.infoLabels["year"] = '-'
        else:
            new_item.action = self.tv_action
            new_item.contentSerieName = new_item.title
            new_item.contentType = 'tvshow'

        return new_item

    def add_serie_to_videolibrary(self, item, itemlist):

        if config.get_videolibrary_support() and len(itemlist) > 0:
            item.url = self.do_url_replace(item.url)
            
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_serie_to_library",
                                 extra="episodios",
                                 contentType='tvshow', 
                                 contentSerieName=item.contentSerieName
                                 )
                            )
        return itemlist

    def do_url_replace(self, url):
        
        if self.url_replace:

            for url_from, url_to in self.url_replace:
                url = re.sub(url_from, url_to, url)

        return url
        
    def do_quote(self, url):
        
        return urlparse.quote_plus(url)
        
    def do_unquote(self, url):
        
        return urlparse.unquote(url)
    
    def list_all_json(self, item, postprocess=None, lim_max=20, is_tvshow=False):
        logger.info()

        itemlist = list()

        json = self.create_soup(item.url, soup=False).json
        
        for key, elem in list(json.items()):

            new_item = Item(channel=item.channel,
                            url=elem.get('url', ''),
                            title=elem.get('title', ''),
                            thumbnail=elem.get('thumb', '') or elem.get('img', ''),
                            infoLabels={"year": elem.get('year', '-')}
                            )
            if postprocess:
                new_item = postprocess(json, elem, new_item, item)

            new_item = self.define_content_type(new_item, is_tvshow=is_tvshow)
            
            new_item.url = self.do_url_replace(new_item.url)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)
    
        return itemlist

    def parse_finds_dict(self, soup, finds, year=False, next_page=False, langs=False, season=False, c_type=''):

        if year:
            matches = '-'
            year_a = ''
            year_b = ''

            try:
                if finds.get('year', []):
                    year_a = finds['year'][0]
                    year_b = finds['year'][1]
                if c_type:
                    if c_type == 'peliculas' and finds.get('year_movie', []):
                        year_a = finds.get('year_movie', [])[0]
                        year_b = finds.get('year_movie', [])[1]
                    elif c_type == 'series' and finds.get('year_serie', []):
                        year_a = finds.get('year_serie', [])[0]
                        year_b = finds.get('year_serie', [])[1]
                    elif c_type == 'episodios' and finds.get('year_episode', []):
                        year_a = finds.get('year_episode', [])[0]
                        year_b = finds.get('year_episode', [])[1]

                if year_a and year_b:
                    matches = soup.find(year_a, class_=year_b).text.strip()
                    if len(matches) > 4:
                        matches = scrapertools.find_single_match(matches, '\d{4}$')
                    matches = int(matches)
                    if matches < 1900 or matches > 2050:
                        matches = '-'
                else:
                    matches = '-'

            except:
                matches = '-'
                logger.error(traceback.format_exc())

        elif next_page:
            matches = ''

            try:
                matches = soup.find(finds['next_page'][0], class_=finds['next_page'][1])
                if finds.get('next_page_all', []):
                    if len(finds['next_page_all']) == 1:
                        matches = matches.find_all(finds['next_page_all'][0])
                    else:
                        matches = matches.find_all(finds['next_page_all'][0], class_=finds['next_page_all'][1])
                    if len(finds['next_page_all']) > 2:
                        for n_page in matches:
                            if finds['next_page_all'][2] in str(n_page):
                                matches = n_page['href']
                                break
                    else:
                        matches = matches[-1]['href']
                matches = urlparse.urljoin(self.host, matches)
            except:
                matches = ''
                logger.error(traceback.format_exc())

        elif langs:
            matches = []
            
            try:
                matches = soup.find(finds['langs'][0], class_=finds['langs'][1])
                if finds.get('langs_all', []):
                    if len(finds['langs_all']) == 1:
                        matches = matches.find_all(finds['langs_all'][0])
                    else:
                        matches = matches.find_all(finds['langs_all'][0], class_=finds['langs_all'][1])
            except:
                matches = []
                logger.error(traceback.format_exc())

        elif season:
            matches = []
            
            try:
                matches = soup.find(finds['season'][0], class_=finds['season'][1])
                if finds.get('season_all', []):
                    if len(finds['season_all']) == 1:
                        matches = matches.find_all(finds['season_all'][0])
                    else:
                        matches = matches.find_all(finds['season_all'][0], class_=finds['season_all'][1])
            except:
                matches = []
                logger.error(traceback.format_exc())

        else:
            matches = []

            try:
                matches = soup.find(finds['find'][0], class_=finds['find'][1])
                if finds.get('find_all', []):
                    if len(finds['find_all']) == 1:
                        matches = matches.find_all(finds['find_all'][0])
                    else:
                        matches = matches.find_all(finds['find_all'][0], class_=finds['find_all'][1])
                if finds.get('find_all_2', []):
                    for f in finds['find_all_2']:
                        matches = matches.find_all(f)
            except:
                matches = []
                logger.error(traceback.format_exc())

        return matches


class CustomChannel(AlfaChannelHelper):
    pass


class DictionaryChannel(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=30, finds={}):
        logger.info()

        if not finds: finds = self.finds
        itemlist = list()
        
        soup = self.create_soup(item.url)
        
        matches = self.parse_finds_dict(soup, finds)
        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)

        next_page = self.parse_finds_dict(soup, finds, next_page=True, c_type=item.c_type)

        for elem in matches:
            try:
                url = urlparse.urljoin(self.host, elem.a["href"])
                title = elem.find("img")["alt"]
            except:
                logger.error(elem)
                continue
            try:
                thumb = elem.find("img")["data-src"]
            except:
                thumb = elem.find("img")["src"]
            thumb = urlparse.urljoin(self.host, thumb)

            year = self.parse_finds_dict(elem, finds, year=True, c_type=item.c_type)

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            if item.c_type == 'episodios':
                new_item.contentType = 'episode'
                try:
                    sxe = elem.find(finds['season_episode'][0], class_=finds['season_episode'][1])
                    if finds.get('season_episode_2', []):
                        for tag in finds['season_episode_2']:
                            sxe = sxe.find(finds['season_episode_2'])
                    new_item.contentSeason, new_item.contentEpisodeNumber = sxe.text.split('x')
                    new_item.contentSeason = int(new_item.contentSeason)
                    new_item.contentEpisodeNumber = int(new_item.contentEpisodeNumber)
                except:
                    new_item.contentSeason = 1
                    new_item.contentEpisodeNumber = 1
                    logger.error(traceback.format_exc())

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item = self.define_content_type(new_item)

            new_item.url = self.do_url_replace(new_item.url)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all',
                                 c_type=item.c_type, 
                                 next_limit=next_limit
                                 )
                               )
        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None, section_list={}, finds={}):
        logger.info()

        if not finds: finds = self.finds
        itemlist = list()
        matches = list()
        soup = {}

        reverse = True if section == "year" else False

        if section_list:
            for genre, url in list(section_list.items()):
                title = genre.capitalize()
                matches.append([title, url])

        elif finds:
            soup = self.create_soup(item.url)

            matches = self.parse_finds_dict(soup, finds)
            for elem in matches:
                title = elem.a.text
                url = elem.a["href"]
                matches.append([title, url])

        if not matches:
            logger.error(finds)
            logger.error(soup or section_list)
            return itemlist

        for title, _url in matches:
            url = urlparse.urljoin(self.host, _url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)

            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None, finds={}):
        logger.info()

        if not finds: finds = self.finds
        itemlist = list()
        item.url = self.do_url_replace(item.url)
        
        soup = self.create_soup(item.url)
        
        matches = self.parse_finds_dict(soup, finds, season=True)

        if not matches:
            logger.error(finds)
            logger.error(soup)
            return itemlist

        infolabels = item.infoLabels

        for elem in matches:
            try:
                infolabels["season"] = int(elem["value"])
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'

            new_item = Item(channel=item.channel,
                            url=item.url, 
                            title=title,
                            action='episodesxseason',
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None, json=True, finds={}):
        logger.info()
        
        if not finds: finds = self.finds
        itemlist = list()
        item.url = self.do_url_replace(item.url)

        infolabels = item.infoLabels
        season = infolabels["season"]

        if json:
            soup = jsontools.load(self.create_soup(item.url).find(finds.get('findvideos', '')[0], 
                                                                  id=finds.get('findvideos', '')[1]).text)
            
            matches = soup.get('props', {}).get('pageProps', {}).get('post', {})\
                          .get('seasons', {})[int(infolabels['season'])-1].get('episodes', {})

            if not matches:
                logger.error(finds)
                logger.error(soup)
                return itemlist

            for elem in matches:
                try:
                    url = finds.get('episode_url', '') % (self.host, elem.get('slug', {}).get('name', ''), 
                                                          infolabels['season'], elem.get('slug', {}).get('episode', ''))
                    title = elem['title']
                except:
                    continue
                try:
                    infolabels["episode"] = int(elem['number'])
                except:
                    infolabels["episode"] = 1
                infolabels["mediatype"] = 'episode'
                title = "%sx%s - %s" % (season, infolabels["episode"], title)

                new_item = Item(channel=item.channel,
                                title=title,
                                url=url,
                                action=action,
                                infoLabels=infolabels
                                )

                if postprocess:
                    new_item = postprocess(soup, elem, new_item, item)

                new_item.url = self.do_url_replace(new_item.url)
                
                itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None, finds={}):

        if not finds: finds = self.finds
        options = list()
        results = list()
        url = self.do_url_replace(url)

        soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)
        
        langs = self.parse_finds_dict(soup, finds, langs=True)
        matches = self.parse_finds_dict(soup, finds)
        
        if not matches or not langs:
            logger.error(finds)
            logger.error(soup)
            return results
        
        for x, _lang in enumerate(langs):
            lang = _lang.find("span").text.lower()
            if 'descargar' in lang: continue
            if 'latino' in lang:
                lang = 'latino'
            elif 'español' in lang:
                lang = 'castellano'
            elif 'subtitulado' in lang:
                lang = 'subtitulado'
            
            for opt in matches[x].find_all("li"):
                options.append((lang, opt))

        results.append([soup, options])

        return results[0]


class DooPlay(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=20):
        logger.info()

        itemlist = list()
        block = list()

        try:
            soup = self.create_soup(item.url)

            if soup.find("div", id="archive-content"):
                block = soup.find("div", id="archive-content")
            elif soup.find("div", class_="content"):
                block = soup.find("div", class_="content")
            matches = block.find_all("article", class_="item")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)

        try:
            if not next_page:
                next_page = soup.find("div", class_="pagination").find("span", class_="current").next_sibling["href"]
                next_page = urlparse.urljoin(self.host, next_page)
        except:
            pass

        for elem in matches:
            try:
                poster = elem.find("div", class_="poster")
                metadata = elem.find("div", class_="metadata")
                data = elem.find("div", class_="data")
                thumb = poster.img["src"]
                title = poster.img["alt"]
                url = poster.find_all("a")[-1]["href"]
                url = urlparse.urljoin(self.host, url)
            except:
                logger.error(elem)
                continue
            try:
                year = int(metadata.find("span", text=re.compile(r"\d{4}")).text.strip())
            except:
                try:
                    year = int(data.find("span", text=re.compile(r"\d{4}")).text.strip())
                except:
                    year = "-"
            if len(str(year)) > 4:
                if scrapertools.find_single_match(str(year), r"(\d{4})"):
                    year = int(scrapertools.find_single_match(str(year), r"(\d{4})"))
                else:
                    year = "-"

            is_tvshow = True if "tvshows" in elem["class"] else False

            new_item = Item(channel=item.channel,
                            url=url,
                            title=title,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )
            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item = self.define_content_type(new_item, is_tvshow=is_tvshow)
            
            new_item.url = self.do_url_replace(new_item.url)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action="list_all",
                                 next_limit=next_limit
                                 )
                            )

        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()

        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
            elif section.lower() == "genres":
                matches = soup.find("ul", class_="genres")
            elif section.lower() == "year":
                matches = soup.find("ul", class_="releases")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text
            if section == "genre":
                title = re.sub(r"\d+(?!\w)|\.", "", elem.a.text)

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )
            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        return itemlist

    def seasons(self, item, action="episodesxseason", post=None, postprocess=None):
        
        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            if post:
                soup = self.create_soup(self.doo_url, post=post)
            else:
                soup = self.create_soup(item.url)

            matches = soup.find("div", id="seasons").find_all("div", class_="se-c")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels

        for elem in matches:
            try:
                infolabels["season"] = int(elem.find("span", class_="se-t").text)
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'

            new_item = Item(channel=item.channel,
                            title=title,
                            url=item.url,
                            action=action,
                            infoLabels=infolabels
                            )
            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", post=None, postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            if post:
                soup = self.create_soup(self.doo_url, post=post)
            else:
                soup = self.create_soup(item.url)

            matches = soup.find("div", id="seasons").find_all("div", class_="se-c")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels

        season = infolabels["season"]

        for elem in matches:
            if elem.find("span", class_="se-t").text != str(season):
                continue

            epi_list = elem.find("ul", class_="episodios").find_all("li", class_=True)
            if not epi_list:
                epi_list = elem.find("ul", class_="episodios").find_all("li")

            for epi in epi_list:
                try:
                    info = epi.find("div", class_="episodiotitle")
                    url = info.a["href"]
                    epi_name = info.a.text
                except:
                    continue
                try:
                    infolabels["episode"] = int(epi.find("div", class_="numerando").text.split(" - ")[1])
                except:
                    infolabels["episode"] = 1
                infolabels["mediatype"] = 'episode'
                title = "%sx%s - %s" % (season, infolabels["episode"], epi_name)

                new_item = Item(channel=item.channel,
                                title=title,
                                url=url,
                                action=action,
                                infoLabels=infolabels
                                )
                if postprocess:
                    new_item = postprocess(soup, elem, new_item, item)

                new_item.url = self.do_url_replace(new_item.url)
                
                itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def search_results(self, item, action="findvideos", postprocess=None, next_pag=False):
        logger.info()

        itemlist = list()

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("div", class_="result-item")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist
        
        try:
            next_page = soup.find("div", class_="pagination").find("span", class_="current").next_sibling["href"]
            next_page = urlparse.urljoin(self.host, next_page)
        except:
            next_page = ''

        for elem in matches:
            url = elem.a.get("href", '')
            if not url: continue
            thumb = elem.img["src"]
            title = elem.img["alt"]
            try:
                year = int(elem.find("span", class_="year").text)
            except:
                year = "-"

            new_item = Item(channel=item.channel,
                            title=title,
                            contentTitle=title,
                            url=url,
                            thumbnail=thumb,
                            action=action,
                            infoLabels={"year": year})

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item = self.define_content_type(new_item)
            
            new_item.url = self.do_url_replace(new_item.url)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page and next_pag:
            itemlist.append(item.clone(title="Siguiente >>",
                                         url=next_page,
                                         action="search_more"
                                         )
                            )

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):

        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)
            
            if soup.find("nav", class_="player"):
                options = soup.find("ul", class_="options")
            else:
                options = soup.find(id=re.compile("playeroptions"))

            matches = options.find_all("li")
        except:
            matches = []
            logger.error(traceback.format_exc())

        results.append([soup, matches])

        return results[0]

    def get_data_by_post(self, elem=None, post=None, custom_url=""):
        
        if not post:
            post = {"action": "doo_player_ajax",
                    "post": elem["data-post"],
                    "nume": elem["data-nume"],
                    "type": elem["data-type"]
                    }

        if custom_url:
            self.doo_url = self.do_url_replace(custom_url)

        data = httptools.downloadpage(self.doo_url, post=post, add_referer=True, soup=True, ignore_response_code=True)

        return data


class ToroFilm(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=20):
        logger.info()

        itemlist = list()
        
        try:
            soup = self.create_soup(item.url)
            matches = soup.find("ul", class_="post-lst").find_all("article", class_="post")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)

        if not next_page:
            try:
                next_page = soup.find("div", class_="nav-links").find_all("a")[-1]["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            try:
                url = urlparse.urljoin(self.host, elem.a["href"])
                title = elem.h2.text
            except:
                logger.error(elem)
                continue
            try:
                thumb = elem.find("img")["data-src"]
            except:
                thumb = elem.find("img")["src"]

            try:
                year = int(elem.find("span", class_="year").text)
            except:
                year = '-'

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item = self.define_content_type(new_item)
            
            new_item.url = self.do_url_replace(new_item.url)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all',
                                 next_limit=next_limit
                                 )
                               )
        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()

        reverse = True if section == "year" else False
        
        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
            elif section:
                if section == "alpha":
                    matches = soup.find("ul", class_="az-lst")
                elif section == "year":
                    matches = soup.find("section", id=re.compile(r"torofilm_movies_annee-\d+"))
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)
        
        if reverse:
            return itemlist[::-1]
        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("li", class_="sel-temp")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels

        for elem in matches:
            try:
                infolabels["season"] = int(elem.a["data-season"])
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'
            post_id = elem.a["data-post"]

            new_item = Item(channel=item.channel,
                            title=title,
                            action='episodesxseason',
                            post_id=post_id,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        infolabels = item.infoLabels
        season = infolabels["season"]

        post = {"action": "action_select_season",
                "season": season,
                "post": item.post_id
                }
        
        try:
            soup = self.create_soup(self.doo_url, post=post)

            matches = soup.find_all("li")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches:
            try:
                url = elem.a["href"]
                title = elem.find("span", class_="num-epi").text
            except:
                continue
            try:
                infolabels["episode"] = int(title.split("x")[1])
            except:
                infolabels["episode"] = 1
            infolabels["mediatype"] = 'episode'
            title = "%sx%s - %s" % (season, infolabels["episode"], title)

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):

        options = list()
        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)

            matches = soup.find_all("ul", class_="aa-tbs aa-tbs-video")
        except:
            matches = []
            logger.error(traceback.format_exc())

        for opt in matches:
            options.extend(opt.find_all("li"))

        results.append([soup, options])

        return results[0]


class ToroPdon(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=24):
        logger.info()

        itemlist = list()
        
        try:
            soup = self.create_soup(item.url)
            if item.c_type == 'episodios':
                matches = soup.find("ul", class_="MovieList Rows episodes").find_all("li", class_="TPostMv")
            else:
                matches = soup.find("ul", class_="MovieList Rows").find_all("div", class_="TPost C hentry")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)

        if not next_page:
            try:
                #next_page = soup.find("div", class_="nav-links").find_all("a")[-1]["href"]
                next_page = soup.find("div", class_="nav-links").find("a", class_="next page-numbers")["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            try:
                url = urlparse.urljoin(self.host, elem.a["href"])
                title = elem.find("img")["alt"]
            except:
                logger.error(elem)
                continue
            try:
                thumb = elem.find("img")["data-src"]
            except:
                thumb = elem.find("img")["src"]
            thumb = urlparse.urljoin(self.host, thumb)

            try:
                if item.c_type == 'episodios':
                    year = '-'
                else:
                    year = int(elem.find("span", class_="Year").text)
            except:
                year = '-'

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            if item.c_type == 'episodios':
                new_item.contentSeason, new_item.contentEpisodeNumber = elem.find("span", class_="Year").text.split('x')
                new_item.contentType = 'episode'
            
            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item = self.define_content_type(new_item)

            new_item.url = self.do_url_replace(new_item.url)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all',
                                 c_type=item.c_type, 
                                 next_limit=next_limit
                                 )
                               )
        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()

        reverse = True if section == "year" else False
        
        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
            elif section:
                if section == "alpha":
                    matches = soup.find("ul", class_="az-lst")
                elif section == "year":
                    matches = soup.find("section", id=re.compile(r"torofilm_movies_annee-\d+"))
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)
        
        if reverse:
            return itemlist[::-1]
        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find("select", id="select-season").find_all('option')
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels

        for elem in matches:
            try:
                infolabels["season"] = int(elem["value"])
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'

            new_item = Item(channel=item.channel,
                            url=item.url, 
                            title=title,
                            action='episodesxseason',
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        infolabels = item.infoLabels
        season = infolabels["season"]

        try:
            soup = jsontools.load(self.create_soup(item.url).find("script", id="__NEXT_DATA__").text)
            matches = soup['props']['pageProps']['thisSerie']['seasons'][int(infolabels['season'])-1]['episodes']
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches:
            try:
                url = '%sepisodio/%s-temporada-%s-episodio-%s' % (self.host, elem['slug']['name'], infolabels['season'], elem['slug']['episode'])
                title = elem['title']
            except:
                continue
            try:
                infolabels["episode"] = int(elem['number'])
            except:
                infolabels["episode"] = 1
            infolabels["mediatype"] = 'episode'
            title = "%sx%s - %s" % (season, infolabels["episode"], title)

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):

        options = list()
        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)
            langs = soup.find_all("div", class_="_1R6bW_0")
            matches = soup.find_all("ul", class_="sub-tab-lang _3eEG3_0 optm3 hide")
        except:
            matches = []
            logger.error(traceback.format_exc())
        
        for x, _lang in enumerate(langs):
            lang = _lang.find("span").text.lower()
            if 'descargar' in lang: continue
            if 'latino' in lang:
                lang = 'latino'
            elif 'español' in lang:
                lang = 'castellano'
            elif 'subtitulado' in lang:
                lang = 'subtitulado'
            
            for opt in matches[x].find_all("li"):
                options.append((lang, opt))

        results.append([soup, options])

        return results[0]


class ToroPlay(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=20):
        logger.info()

        itemlist = list()
        
        try:
            soup = self.create_soup(item.url)
            matches = soup.find("ul", class_="MovieList").find_all("article", class_=re.compile("TPost C"))
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            try:
                url = urlparse.urljoin(self.host, elem.a["href"])
                title = elem.a.h3.text
                thumb = elem.find("img")
                thumb = thumb["data-src"] if thumb.has_attr("data-src") else thumb["src"]
            except:
                logger.error(elem)
                continue
            try:
                year = scrapertools.find_single_match(title, r'\((\d{4})\)')
                if not year:
                    year = elem.find("span", class_="Year").text
                year = int(year)
            except:
                year = "-"

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all',
                                 next_limit=next_limit
                                 )
                            )

        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()
        reverse = True if section == "year" else False

        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
            elif section:
                if section == "genres":
                    matches = soup.find(id=re.compile(r"categories-\d+"))
                elif section == "alpha":
                    matches = soup.find("ul", class_="AZList")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def list_alpha(self, item, action="season", postprocess=None):

        itemlist = list()

        try:
            soup = self.create_soup(item.url)
            matches = soup.find("tbody").find_all("tr")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist
        
        matches, next_limit, next_page = self.limit_results(item, matches)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            info = elem.find("td", class_="MvTbTtl")
            thumb = elem.find("td", class_="MvTbImg").a.img["src"]
            url = info.a["href"]
            title = info.a.text.strip()
            try:
                year = int(elem.find("td", text=re.compile(r"\d{4}")).string)
            except:
                year = "-"

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_alpha',
                                 next_limit=next_limit
                                 )
                            )

        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        
        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("div", class_="Wdgt AABox")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels
        for elem in matches:
            try:
                infolabels["season"] = int(elem.find("div", class_="AA-Season")["data-tab"])
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'

            new_item = Item(channel=item.channel,
                            title=title,
                            url=item.url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("div", class_="Wdgt AABox")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels
        season = infolabels["season"]

        for elem in matches:
            if elem.find("div", class_="AA-Season")["data-tab"] == str(season):
                epi_list = elem.find_all("tr")
                for epi in epi_list:
                    try:
                        url = epi.a["href"]
                        epi_name = epi.find("td", class_="MvTbTtl").a.text
                    except:
                        continue
                    try:
                        infolabels["episode"] = int(epi.find("span", class_="Num").text)
                    except:
                        infolabels["episode"] = 1
                    infolabels["mediatype"] = 'episode'
                    title = "%sx%s - %s" % (season, infolabels["episode"], epi_name)

                    new_item = Item(channel=item.channel,
                                    title=title,
                                    url=url,
                                    action=action,
                                    infoLabels=infolabels
                                    )

                    if postprocess:
                        new_item = postprocess(soup, elem, new_item, item)

                    new_item.url = self.do_url_replace(new_item.url)
                    
                    itemlist.append(new_item)
                break

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):
        
        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)

            matches = soup.find("ul", class_="TPlayerNv").find_all("li")
        except:
            matches = []
            logger.error(traceback.format_exc())

        results.append([soup, matches])

        return results[0]


class ToroFlix(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=20):
        logger.info()

        itemlist = list()
        
        try:
            soup = self.create_soup(item.url)
            matches = soup.find("ul", class_="MovieList").find_all("article", class_=re.compile("TPost B"))
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            try:
                url = urlparse.urljoin(self.host, elem.a["href"])
                title = elem.find(class_="Title").text
                thumb = elem.find("img")
                thumb = thumb["data-src"] if thumb.has_attr("data-src") else thumb["src"]
            except:
                logger.error(elem)
                continue
            try:
                year = int(elem.find("span", class_="Date").text)
            except:
                year = "-"

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all'
                                 )
                            )

        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()
        reverse = True if section == "year" else False

        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
            elif section:
                if section == "genres":
                    matches = soup.find(id=(r"toroflix_genres_widget-2"))
                elif section == "alpha":
                    matches = soup.find("ul", class_="AZList")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def list_alpha(self, item, action="season", postprocess=None):

        itemlist = list()

        try:
            soup = self.create_soup(item.url)
            matches = soup.find("tbody").find_all("tr")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            info = elem.find("td", class_="MvTbTtl")
            thumb = elem.find("td", class_="MvTbImg").a.img["src"]
            url = info.a["href"]
            title = info.a.text.strip()
            try:
                year = int(elem.find("td", text=re.compile(r"\d{4}")).string)
            except:
                year = "-"
            
            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_alpha',
                                 next_limit=next_limit
                                 )
                            )

        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        
        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("section", class_="SeasonBx AACrdn")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels

        for elem in matches:
            try:
                infolabels["season"] = int(elem.a.span.text)
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'
            url = elem.a["href"]

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("tr", class_="Viewed")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels
        season = infolabels["season"]

        for elem in matches:
            try:
                url = elem.find("td", class_="MvTbTtl").a["href"]
                epi_name = elem.find("td", class_="MvTbTtl").a.text
            except:
                continue
            try:
                infolabels["episode"] = int(elem.find("span", class_="Num").text)
            except:
                infolabels["episode"] = 1
            infolabels["mediatype"] = 'episode'
            title = "%sx%s - %s" % (season, infolabels["episode"], epi_name)

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                           )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):
        
        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)
            
            if soup.find("div", class_="optns-bx"):
                matches = soup.find_all("button")
            else:
                matches = soup.find("ul", class_="ListOptions").find_all("li")
        except:
            matches = []
            logger.error(traceback.format_exc())

        results.append([soup, matches])

        return results[0]


class PsyPlay(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=20):
        logger.info()

        itemlist = list()

        try:
            soup = self.create_soup(item.url)
            matches = soup.find("div", class_="movies-list").find_all("div", class_="ml-item")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)
        if not next_page:
            try:
                item.url = re.sub(r"page/\d+/", "", item.url)
                next_page = soup.find("ul", class_="pagination").find("li", class_="active").next_sibling.a.text
                next_page = urlparse.urljoin(self.host, "page/%s/" % next_page)
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            try:
                thumb = urlparse.urljoin(self.host, elem.a.img.get("src", '') or elem.a.img.get("data-original", ''))
                title = elem.a.find("span", class_="mli-info").h2.text
                url = urlparse.urljoin(self.host, elem.a["href"])
            except:
                logger.error(elem)
                continue

            try:
                year = int(elem.find("div", class_="jt-info", text=re.compile("\d{4}")).text)
            except:
                year = "-"

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year})

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all'
                                 )
                            )

        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()
        reverse = True if section == "year" else False

        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        
        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find("div", id="seasons").find_all("div", recursive=False)
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels

        for elem in matches:
            try:
                infolabels["season"] = int(scrapertools.find_single_match(elem.text, r"(\d+)"))
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'

            new_item = Item(channel=item.channel,
                            title=title,
                            url=item.url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)

            infolabels = item.infoLabels
            season = infolabels["season"]

            matches = soup.find("div", id="seasons").find_all("div", recursive=False)[int(season) - 1].find_all("a")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches:
            try:
                url = elem["href"]
            except:
                continue
            try:
                infolabels["episode"] = int(scrapertools.find_single_match(elem.text, r"(\d+)"))
            except:
                infolabels["episode"] = 1
            infolabels["mediatype"] = 'episode'
            title = "%sx%s - " % (season, infolabels["episode"])

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):
        
        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)
        
            matches = soup.find("ul", class_="idTabs").find_all("li")
        except:
            matches = []
            logger.error(traceback.format_exc())

        results.append([soup, matches])

        return results[0]
