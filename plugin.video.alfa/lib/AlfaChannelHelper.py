# -*- coding: utf-8 -*-
# -*- Alfa Channel Helper -*-
# -*- Herramientas genericas para canales BS -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from core import httptools
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import config
from platformcode import logger


class AlfaChannelHelper:

    def __init__(self, host, movie_path="/movies", tv_path="/serie", movie_action="findvideos", tv_action="seasons"):
        self.host = host
        self.movie_path = movie_path
        self.tv_path = tv_path
        self.movie_action = movie_action
        self.tv_action = tv_action
        self.doo_url = "%swp-admin/admin-ajax.php" % host

    def create_soup(self, url, **kwargs):
        """
        :param url: url destino
        :param kwargs: parametros que se usan en donwloadpage
        :return: objeto soup
        """

        kwargs["soup"] = True
        soup = httptools.downloadpage(url, **kwargs).soup
        return soup

    def list_all(self, item, postprocess=None):
        pass

    def limit_results(self, item, matches):

        next_page = None
        next_limit = None

        if len(matches) > 20 and not item.next_limit:
            limit = int(len(matches) / 2)
            next_limit = limit + 1
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

    def get_video_options(self, url):
        pass

    def define_content_type(self, new_item, is_tvshow=False):

        if new_item.infoLabels["year"] in new_item.title:
            new_item.title = re.sub("\(|\)|%s" % new_item.infoLabels["year"], "", new_item.title)

        if not is_tvshow and (self.movie_path in new_item.url or not self.tv_path in new_item.url):
            new_item.action = self.movie_action
            new_item.contentTitle = new_item.title
        else:
            new_item.action = self.tv_action
            new_item.contentSerieName = new_item.title

        return new_item

    def add_serie_to_videolibrary(self, item, itemlist):

        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_serie_to_library",
                                 extra="episodios",
                                 contentSerieName=item.contentSerieName
                                 )
                            )
        return itemlist


class DooPlay(AlfaChannelHelper):

    def list_all(self, item, postprocess=None):
        logger.info()

        itemlist = list()
        block = list()

        soup = self.create_soup(item.url)

        if soup.find("div", id="archive-content"):
            block = soup.find("div", id="archive-content")
        elif soup.find("div", class_="content"):
            block = soup.find("div", class_="content")
        matches = block.find_all("article", class_="item")

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)

        try:
            if not next_page:
                next_page = soup.find("div", class_="pagination").find("span", class_="current").next_sibling["href"]
                if not next_page.startswith("http"):
                    next_page = item.url + next_page
        except:
            pass

        for elem in matches:

            poster = elem.find("div", class_="poster")
            metadata = elem.find("div", class_="metadata")
            data = elem.find("div", class_="data")
            thumb = poster.img["src"]
            title = poster.img["alt"]
            url = poster.find_all("a")[-1]["href"]
            url = url if url.startswith("http") else self.host + url
            try:
                year = metadata.find("span", text=re.compile(r"\d{4}")).text.strip()
            except:
                try:
                    year = data.find("span", text=re.compile(r"\d{4}")).text.strip()
                except:
                    year = "-"
            if len(year) > 4:
                year = scrapertools.find_single_match(year, r"(\d{4})")

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

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        if next_page:

            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action="list_all",
                                 next_limit=next_limit,
                                 )
                            )

        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()

        soup = self.create_soup(item.url)

        if menu_id:
            matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
        elif section.lower() == "genres":
            matches = soup.find("ul", class_="genres")
        elif section.lower() == "year":
            matches = soup.find("ul", class_="releases")

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text
            if section == "genre":
                title = re.sub(r"\d+(?!\w)|\.", "", elem.a.text)

            if not url.startswith("http"):
                url = self.host + url

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )
            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        return itemlist

    def seasons(self, item, action="episodesxseason", post=None, postprocess=None):
        itemlist = list()

        if post:
            soup = self.create_soup(self.doo_url, post=post)
        else:
            soup = self.create_soup(item.url)

        matches = soup.find("div", id="seasons").find_all("div", class_="se-c")

        infolabels = item.infoLabels

        for elem in matches:
            season = elem.find("span", class_="se-t").text
            title = "Temporada %s" % season
            infolabels["season"] = season

            new_item = Item(channel=item.channel,
                            title=title,
                            url=item.url,
                            action=action,
                            infoLabels=infolabels
                            )
            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", post=None, postprocess=None):
        logger.info()

        itemlist = list()

        if post:
            soup = self.create_soup(self.doo_url, post=post)
        else:
            soup = self.create_soup(item.url)

        matches = soup.find("div", id="seasons").find_all("div", class_="se-c")

        infolabels = item.infoLabels

        season = infolabels["season"]

        for elem in matches:
            if elem.find("span", class_="se-t").text != str(season):
                continue

            epi_list = elem.find("ul", class_="episodios").find_all("li", class_=True)
            if not epi_list:
                epi_list = elem.find("ul", class_="episodios").find_all("li")

            for epi in epi_list:

                info = epi.find("div", class_="episodiotitle")
                url = info.a["href"]
                epi_name = info.a.text
                epi_num = epi.find("div", class_="numerando").text.split(" - ")[1]
                infolabels["episode"] = epi_num
                title = "%sx%s - %s" % (season, epi_num, epi_name)

                new_item = Item(channel=item.channel,
                                title=title,
                                url=url,
                                action=action,
                                infoLabels=infolabels
                                )
                if postprocess:
                    new_item = postprocess(soup, elem, new_item, item)

                itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def search_results(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()

        soup = self.create_soup(item.url)
        matches = soup.find_all("div", class_="result-item")

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)

        for elem in matches:
            url = elem.a["href"]
            thumb = elem.img["src"]
            title = elem.img["alt"]
            try:
                year = elem.find("span", class_="year").text
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


            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:

            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action="search_results",
                                 next_limit=next_limit,
                                 )
                            )

        return itemlist

    def get_video_options(self, url):

        results = list()

        soup = self.create_soup(url)
        if soup.find("nav", class_="player"):
            options = soup.find("ul", class_="options")
        else:
            options = soup.find(id=re.compile("playeroptions"))

        try:
            matches = options.find_all("li")
        except:
            matches = "No Options Found"

        results.append([soup, matches])

        return results[0]

    def get_data_by_post(self, elem=None, post=None):
        if not post:
            post = {"action": "doo_player_ajax",
                    "post": elem["data-post"],
                    "nume": elem["data-nume"],
                    "type": elem["data-type"]
                    }

        data = httptools.downloadpage(self.doo_url, post=post, add_referer=True, soup=True)

        return data


class ToroFilm(AlfaChannelHelper):

    def list_all(self, item, postprocess=None):
        logger.info()

        itemlist = list()
        soup = self.create_soup(item.url)
        matches = soup.find("ul", class_="post-lst").find_all("article", class_="post")

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)

        if not next_page:
            try:
                next_page = soup.find("div", class_="nav-links").find_all("a")[-1]["href"]
                if not next_page.startswith("http"):
                    next_page = item.url + next_page
            except:
                pass

        for elem in matches:
            url = elem.a["href"] if elem.a["href"].startswith("http") else self.host + elem.a["href"]
            title = elem.h2.text
            try:
                thumb = elem.find("img")["data-src"]
            except:
                thumb = elem.find("img")["src"]

            try:
                year = elem.find("span", class_="year").text
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
        soup = self.create_soup(item.url)

        if menu_id:
            matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
        elif section:
            if section == "alpha":
                matches = soup.find("ul", class_="az-lst")
            elif section == "year":
                matches = soup.find("section", id=re.compile(r"torofilm_movies_annee-\d+"))

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            if not url.startswith("http"):
                url = self.host + url

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)
        if reverse:
            return itemlist[::-1]
        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        logger.info()

        itemlist = list()

        soup = self.create_soup(item.url)
        matches = soup.find_all("li", class_="sel-temp")

        infolabels = item.infoLabels

        for elem in matches:
            season = elem.a["data-season"]
            post_id = elem.a["data-post"]
            title = "Temporada %s" % season
            infolabels["season"] = season

            new_item = Item(channel=item.channel,
                            title=title,
                            action='episodesxseason',
                            post_id=post_id,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()

        infolabels = item.infoLabels
        season = infolabels["season"]

        post = {"action": "action_select_season",
                "season": season,
                "post": item.post_id
                }
        soup = self.create_soup(self.doo_url, post=post)

        matches = soup.find_all("li")

        for elem in matches:
            url = elem.a["href"]
            title = elem.find("span", class_="num-epi").text
            epi_num = title.split("x")[1]
            infolabels["episode"] = epi_num

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url):

        options = list()
        results = list()

        soup = self.create_soup(url)

        try:
            matches = soup.find_all("ul", class_="aa-tbs aa-tbs-video")

        except:
            matches = "No Options Found"

        for opt in matches:
            options.extend(opt.find_all("li"))

        results.append([soup, options])

        return results[0]


class ToroPlay(AlfaChannelHelper):

    def list_all(self, item, postprocess=None):
        logger.info()

        itemlist = list()
        soup = self.create_soup(item.url)
        matches = soup.find("ul", class_="MovieList").find_all("article", class_=re.compile("TPost C"))

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                if next_page and not next_page.startswith("http"):
                    next_page = item.url + next_page
            except:
                pass

        for elem in matches:
            url = elem.a["href"] if elem.a["href"].startswith("http") else self.host + elem.a["href"]
            title = elem.a.h3.text
            thumb = elem.find("img")
            thumb = thumb["data-src"] if thumb.has_attr("data-src") else thumb["src"]
            year = scrapertools.find_single_match(title, r'\((\d{4})\)')
            if not year:
                try:
                    year = elem.find("span", class_="Year").text
                except:
                    pass
            if not year:
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
        block = list()
        reverse = True if section == "year" else False

        soup = self.create_soup(item.url)

        if menu_id:
            block = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
        elif section:
            if section == "genres":
                block = soup.find(id=re.compile(r"categories-\d+"))
            elif section == "alpha":
                block = soup.find("ul", class_="AZList")

        for elem in block.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            if not url.startswith("http"):
                url = self.host + url

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def list_alpha(self, item, action="season", postprocess=None):

        itemlist = list()

        soup = self.create_soup(item.url)
        matches = soup.find("tbody").find_all("tr")

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                if next_page and not next_page.startswith("http"):
                    next_page = item.url + next_page
            except:
                pass

        for elem in matches:
            info = elem.find("td", class_="MvTbTtl")
            thumb = elem.find("td", class_="MvTbImg").a.img["src"]
            url = info.a["href"]
            title = info.a.text.strip()
            year = "-"
            try:
                year = elem.find("td", text=re.compile(r"\d{4}")).string
            except:
                pass

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

        soup = self.create_soup(item.url)
        matches = soup.find_all("div", class_="Wdgt AABox")

        infolabels = item.infoLabels
        for elem in matches:
            season = elem.find("div", class_="AA-Season")["data-tab"]
            title = "Temporada %s" % season
            infolabels["season"] = season

            new_item = Item(channel=item.channel,
                            title=title,
                            url=item.url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()

        soup = self.create_soup(item.url)
        matches = soup.find_all("div", class_="Wdgt AABox")

        infolabels = item.infoLabels
        season = infolabels["season"]

        for elem in matches:
            if elem.find("div", class_="AA-Season")["data-tab"] == str(season):
                epi_list = elem.find_all("tr")
                for epi in epi_list:
                    try:
                        url = epi.a["href"]
                        epi_num = epi.find("span", class_="Num").text
                        epi_name = epi.find("td", class_="MvTbTtl").a.text
                        infolabels["episode"] = epi_num
                        title = "%sx%s - %s" % (season, epi_num, epi_name)

                        new_item = Item(channel=item.channel,
                                        title=title,
                                        url=url,
                                        action=action,
                                        infoLabels=infolabels
                                        )

                        if postprocess:
                            new_item = postprocess(soup, elem, new_item, item)

                        itemlist.append(new_item)
                    except:
                        pass
                break

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url):
        results = list()

        soup = self.create_soup(url)

        try:
            matches = soup.find("ul", class_="TPlayerNv").find_all("li")
        except:
            matches = "No Options Found"

        results.append([soup, matches])

        return results[0]


class ToroFlix(AlfaChannelHelper):

    def list_all(self, item, postprocess=None):
        logger.info()

        itemlist = list()
        soup = self.create_soup(item.url)
        matches = soup.find("ul", class_="MovieList").find_all("article", class_=re.compile("TPost B"))

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                if next_page and not next_page.startswith("http"):
                    next_page = item.url + next_page
            except:
                pass

        for elem in matches:

            url = elem.a["href"] if elem.a["href"].startswith("http") else self.host + elem.a["href"]
            title = elem.find(class_="Title").text
            thumb = elem.find("img")
            thumb = thumb["data-src"] if thumb.has_attr("data-src") else thumb["src"]
            try:
                year = elem.find("span", class_="Date").text
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
        block = list()
        reverse = True if section == "year" else False

        soup = self.create_soup(item.url)

        if menu_id:
            block = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
        elif section:
            if section == "genres":
                block = soup.find(id=(r"toroflix_genres_widget-2"))
            elif section == "alpha":
                block = soup.find("ul", class_="AZList")

        for elem in block.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            if not url.startswith("http"):
                url = self.host + url

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def list_alpha(self, item, action="season", postprocess=None):

        itemlist = list()

        soup = self.create_soup(item.url)
        matches = soup.find("tbody").find_all("tr")

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                if next_page and not next_page.startswith("http"):
                    next_page = item.url + next_page
            except:
                pass

        for elem in matches:
            info = elem.find("td", class_="MvTbTtl")
            thumb = elem.find("td", class_="MvTbImg").a.img["src"]
            url = info.a["href"]
            title = info.a.text.strip()
            year = "-"
            try:
                year = elem.find("td", text=re.compile(r"\d{4}")).string
            except:
                pass
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

        soup = self.create_soup(item.url)
        matches = soup.find_all("section", class_="SeasonBx AACrdn")

        infolabels = item.infoLabels

        for elem in matches:
            season = elem.a.span.text
            url = elem.a["href"]
            title = "Temporada %s" % season
            infolabels["season"] = season

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()

        soup = self.create_soup(item.url)
        matches = soup.find_all("tr", class_="Viewed")

        infolabels = item.infoLabels
        season = infolabels["season"]

        for elem in matches:

            url = elem.find("td", class_="MvTbTtl").a["href"]
            epi_num = elem.find("span", class_="Num").text
            epi_name = elem.find("td", class_="MvTbTtl").a.text
            infolabels["episode"] = epi_num
            title = "%sx%s - %s" % (season, epi_num, epi_name)

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                           )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url):
        results = list()

        soup = self.create_soup(url)
        if soup.find("div", class_="optns-bx"):
            try:
                matches = soup.find_all("button")
            except:
                matches = "No Options Found"
        else:
            try:
                matches = soup.find("ul", class_="ListOptions").find_all("li")
            except:
                matches = "No Options Found"

        results.append([soup, matches])

        return results[0]


class PsyPlay(AlfaChannelHelper):

    def list_all(self, item, postprocess=None):
        logger.info()

        itemlist = list()

        soup = self.create_soup(item.url)
        matches = soup.find("div", class_="movies-list").find_all("div", class_="ml-item")

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)
        if not next_page:
            try:
                item.url = re.sub(r"page/\d+/", "", item.url)
                next_page = soup.find("ul", class_="pagination").find("li", class_="active").next_sibling.a.text
                next_page = "%s/page/%s/" % (item.url, next_page)
                if next_page and not next_page.startswith("http"):
                    next_page = item.url + next_page
            except:
                pass

        for elem in matches:
            thumb = self.host + elem.a.img["src"] if elem.a.img.has_attr("src") else elem.a.img["data-original"]
            title = elem.a.find("span", class_="mli-info").h2.text
            url = elem.a["href"] if elem.a["href"].startswith("http") else self.host + elem.a["href"]
            try:
                year = elem.find("div", class_="jt-info", text=re.compile("\d{4}")).text
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
        block = list()
        reverse = True if section == "year" else False

        soup = self.create_soup(item.url)

        if menu_id:
            block = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")

        for elem in block.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            if not url.startswith("http"):
                url = self.host + url

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        itemlist = list()

        soup = self.create_soup(item.url)
        matches = soup.find("div", id="seasons").find_all("div", recursive=False)

        infolabels = item.infoLabels

        for elem in matches:

            season = scrapertools.find_single_match(elem.text, r"(\d+)")
            title = "Temporada %s" % season
            infolabels["season"] = season

            new_item = Item(channel=item.channel,
                            title=title,
                            url=item.url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_serie_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()

        soup = self.create_soup(item.url)

        infolabels = item.infoLabels
        season = infolabels["season"]

        matches = soup.find("div", id="seasons").find_all("div", recursive=False)[int(season) - 1].find_all("a")

        for elem in matches:
            url = elem["href"]
            epi_num = scrapertools.find_single_match(elem.text, r"(\d+)")
            infolabels["episode"] = epi_num
            title = "%sx%s" % (season, epi_num)

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url):
        results = list()

        soup = self.create_soup(url)
        try:
            matches = soup.find("ul", class_="idTabs").find_all("li")
        except:
            matches = "No Options Found"

        results.append([soup, matches])

        return results[0]
