# -*- coding: utf-8 -*-

from xml.etree import ElementTree
import urllib.parse
import urllib.request


def find_radar_observation_times(api_key):
    base_url = 'http://data.fmi.fi/fmi-apikey/' + api_key + '/wfs?'
    wfs_params = {
        'request': 'GetFeature',
        'storedquery_id': 'fmi::radar::composite::rr'
    }
    complete_url = base_url + urllib.parse.urlencode(wfs_params)

    with urllib.request.urlopen(complete_url) as response:
        root = ElementTree.fromstring(response.read())

    namespaces = {
        'gml': 'http://www.opengis.net/gml/3.2',
        'om': 'http://www.opengis.net/om/2.0'
    }
    all_times = root.findall('.//om:resultTime//gml:timePosition', namespaces)
    time_strings = [time.text for time in all_times]
    return time_strings
