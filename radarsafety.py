# -*- coding: utf-8 -*-

import configparser
import os
import time_utils
from owslib.wms import WebMapService


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
    rain_rate_layer = wms['suomi_rr_eureffin']
    bounding_box = (-118331.366, 6335621.167, 875567.732, 7907751.537)
    image_data = wms.getmap(layers=[rain_rate_layer.title],
                            srs='EPSG:3067',
                            bbox=bounding_box,
                            size=(994, 1572),
                            time=radar_time_string,
                            styles=['Radar rr'],
                            #styles=['raster'],
                            format='image/png')
    with open('radar.png', 'wb') as outfile:
        outfile.write(image_data.read())


if __name__ == '__main__':
    main()
