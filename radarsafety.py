# -*- coding: utf-8 -*-

import os
import configparser
import urllib.parse
import urllib.request
import time
import io

import PIL.Image
import numpy as np

import time_utils


# Komakallio location in EPSG:3067 coordinates
KOMAKALLIO_EPSG3067 = (355121.064967, 6673513.77179)

# Radar image scale
METERS_PER_PIXEL = 1000.0

# Bounding box size in meters
BOUNDING_BOX_SIZE = 300000.0
BOUNDING_BOX = (KOMAKALLIO_EPSG3067[0] - BOUNDING_BOX_SIZE / 2, KOMAKALLIO_EPSG3067[1] - BOUNDING_BOX_SIZE / 2,
                KOMAKALLIO_EPSG3067[0] + BOUNDING_BOX_SIZE / 2, KOMAKALLIO_EPSG3067[1] + BOUNDING_BOX_SIZE / 2)

# Image size in pixels
IMAGE_SIZE = int(BOUNDING_BOX_SIZE / METERS_PER_PIXEL)


def combine_tuple_to_string(tuple_object):
    output_string = ''
    for item in tuple_object:
        output_string += str(item) + ','
    return output_string[:-1]


def get_circle_mask(center_x, center_y, radius, grid_edge_length):
    y, x = np.ogrid[-center_y:grid_edge_length - center_y, -center_x:grid_edge_length - center_x]
    mask = x * x + y * y <= radius * radius
    return mask


def main():
    # Try to read API key from config file
    if not os.path.isfile('config.ini'):
        print('config.ini not found!')
        return
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        api_key = config['API']['api_key']
    except KeyError:
        print('API key not found in config!')
        return

    # Determine latest radar image time
    latest_radar_time = time_utils.current_radar_time(offset=-5)
    radar_time_string = time_utils.datetime_to_wms_string(latest_radar_time)
    timestamp = int(1000 * time.mktime(latest_radar_time.timetuple()))
    print('Fetching radar image for {}'.format(radar_time_string))
    print('Timestamp: {}'.format(timestamp))

    # Fetch radar image
    base_url = 'http://wms.fmi.fi/fmi-apikey/' + api_key + '/geoserver/Radar/wms?'
    wms_params = {
        'service': 'WMS',
        'version': '1.3.0',
        'request': 'GetMap',
        'layers': 'suomi_rr_eureffin',
        'crs': 'EPSG:3067',
        'bbox': combine_tuple_to_string(BOUNDING_BOX),
        'styles': 'raster',
        'width': IMAGE_SIZE,
        'height': IMAGE_SIZE,
        'format': 'image/png',
        'time': radar_time_string
    }

    complete_url = base_url + urllib.parse.urlencode(wms_params)
    with urllib.request.urlopen(complete_url) as response:
        image = PIL.Image.open(io.BytesIO(response.read()))
    image.save('latest_rain_intensity.png')

    rain_intensity = np.array(image) / 100.0
    max_intensity = rain_intensity.max()
    print('Maximum rain intensity in bounding box: {} mm/h'.format(max_intensity))


if __name__ == '__main__':
    main()
