# -*- coding: utf-8 -*-

from resources.lib import kodiutils
from resources.lib import kodilogging
from urllib.request import urlopen
import io
import os
import sys
import time
import zipfile
import urllib
import logging
import xbmcaddon
import xbmcgui
import xbmc


ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))


class Canceled(Exception):
    pass


def read(response):
    data = b""
    total_size = response.info().get('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    chunk_size = 1024 * 1024
    reader = lambda: response.read(chunk_size)
    for index, chunk in enumerate(iter(reader, b"")):
        data += chunk
    return data


def extract(zip_file, output_directory):
    zin = zipfile.ZipFile(zip_file)
    files_number = len(zin.infolist())
    for index, item in enumerate(zin.infolist()):
        try:
            zin.extract(item, output_directory)
        except Canceled:
            return False
        else:
            zin.extract(item, output_directory)
    return True


def stva():
    addon_name = ADDON.getAddonInfo('name')
    url = 'http://bit.ly/pack-ajustes-v'
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request)
    try:
        data = read(response)
    except Canceled:
        message = "Descarga cancelada"
    else:
        addon_folder = xbmc.translatePath(os.path.join('special://', 'home'))
        if extract(io.BytesIO(data), addon_folder):
            message = "Instalación finalizada con éxito. "
        else:
            message = "Extraccion cancelada"
    dialog = xbmcgui.Dialog()
    dialog.ok(addon_name, "%s, Por favor, cierra la aplicación para completar el proceso" % message)
    os._exit(0)
