# -*- coding: utf-8 -*-

import io
import urllib.parse
import urllib.request

import PIL.Image


def fetch_radar_image(radar_time_string, bounding_box, image_edge_length):
    base_url = 'https://openwms.fmi.fi/geoserver/wms?'
    wms_params = {
        'service': 'WMS',
        'version': '1.3.0',
        'request': 'GetMap',
        'layers': 'suomi_rr_eureffin',
        'crs': 'EPSG:3067',
        'bbox': combine_tuple_to_string(bounding_box),
        'styles': 'raster',
        'width': image_edge_length,
        'height': image_edge_length,
        'format': 'image/png',
        'time': radar_time_string
    }
    complete_url = base_url + urllib.parse.urlencode(wms_params)
    with urllib.request.urlopen(complete_url, timeout=15) as response:
        image = PIL.Image.open(io.BytesIO(response.read()))
    return image


def combine_tuple_to_string(tuple_object):
    output_string = ''
    for item in tuple_object:
        output_string += str(item) + ','
    return output_string[:-1]
