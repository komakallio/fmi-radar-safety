# -*- coding: utf-8 -*-

import configparser
import os
import time_utils
from owslib.wms import WebMapService

# Komakallio location in EPSG:3067 coordinates
KOMAKALLIO_EPSG3067 = (355121.064967, 6673513.77179)

# Radar image scale
METERS_PER_PIXEL = 250.0

# Bounding box size in meters
BOUNDING_BOX_SIZE = 150000.0
BOUNDING_BOX = (KOMAKALLIO_EPSG3067[0] - BOUNDING_BOX_SIZE / 2, KOMAKALLIO_EPSG3067[1] - BOUNDING_BOX_SIZE / 2,
                KOMAKALLIO_EPSG3067[0] + BOUNDING_BOX_SIZE / 2, KOMAKALLIO_EPSG3067[1] + BOUNDING_BOX_SIZE / 2)

# Image size in pixels
IMAGE_SIZE = 2 * (int(BOUNDING_BOX_SIZE / METERS_PER_PIXEL),)


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
    print('Fetching radar image for {}'.format(radar_time_string))

    # Fetch radar image
    base_url = 'http://wms.fmi.fi/fmi-apikey/' + api_key + '/geoserver/Radar/wms'
    wms = WebMapService(base_url, version='1.3.0')
    image_data = wms.getmap(layers=['suomi_rr_eureffin'],
                            srs='EPSG:3067',
                            bbox=BOUNDING_BOX,
                            size=IMAGE_SIZE,
                            time=radar_time_string,
                            styles=['Radar rr'],
                            #styles=['raster'],
                            format='image/png')
    with open('radar.png', 'wb') as outfile:
        outfile.write(image_data.read())


if __name__ == '__main__':
    main()
