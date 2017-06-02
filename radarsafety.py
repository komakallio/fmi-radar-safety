# -*- coding: utf-8 -*-

import configparser
import os
import time
import calendar
import requests

import numpy as np

import wms
import wfs

# Komakallio location in EPSG:3067 coordinates
KOMAKALLIO_EPSG3067 = (355121.064967, 6673513.77179)

# Radar image scale
METERS_PER_PIXEL = 1000.0

# Bounding box edge length in meters
BOUNDING_BOX_SIZE = 300000.0


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

    # Bounding box corner coordinates in EPSG:3067
    bounding_box = (KOMAKALLIO_EPSG3067[0] - BOUNDING_BOX_SIZE / 2, KOMAKALLIO_EPSG3067[1] - BOUNDING_BOX_SIZE / 2,
                    KOMAKALLIO_EPSG3067[0] + BOUNDING_BOX_SIZE / 2, KOMAKALLIO_EPSG3067[1] + BOUNDING_BOX_SIZE / 2)

    # Image edge length in pixels
    image_edge_length = int(BOUNDING_BOX_SIZE / METERS_PER_PIXEL)

    # Determine latest radar image time
    try:
        latest_radar_time = wfs.find_radar_observation_times(api_key)[-1]
    except IndexError:
        print('Radar observation time information not available!')
        return

    # Fetch radar image
    image = wms.fetch_radar_image(latest_radar_time, api_key, bounding_box, image_edge_length)

    # Check if image returned by server is valid
    if image.mode is not 'I':
        print('Image not available!')
        return

    image.save('latest_rain_intensity.png')

    # Calculate maximum rain inside bounding box
    rain_intensity = np.array(image) / 100.0
    max_intensity = rain_intensity.max()
    print('Maximum rain intensity in bounding box: {} mm/h'.format(max_intensity))

    # Calculate maximum rain intensity inside circles of different radii
    api_data = {}
    for radius_km in [50, 30, 10, 3, 1]:
        radius_m = 1000 * radius_km
        max_intensity_inside_circle = max_inside_circle(rain_intensity, radius_m, METERS_PER_PIXEL)
        print('Maximum rain intensity inside {} km: {} mm/h'.format(radius_km, max_intensity_inside_circle))
        api_data['{}km'.format(radius_km)] = max_intensity_inside_circle

    # Report data to Komakallio API
    try:
        report_to_api(api_data, latest_radar_time)
    except ConnectionError as e:
        print(e)
        return


def report_to_api(api_data, iso_time_string):
    timestamp = 1000 * iso_string_to_unix_timestamp(iso_time_string)
    json_data = {
        'Type': 'Radar',
        'Timestamp': timestamp,
        'Data': api_data
    }
    try:
        report_response = requests.post('http://localhost:9001/api', json=json_data)
        print('Komakallio API responded with status {}'.format(report_response.status_code))
    except requests.exceptions.ConnectionError:
        raise ConnectionError('Could not establish connection to Komakallio API!')


def iso_string_to_unix_timestamp(iso_string):
    timestamp = calendar.timegm(time.strptime(iso_string, '%Y-%m-%dT%H:%M:%SZ'))
    return timestamp


def circle_mask(center_x, center_y, radius, grid_edge_length):
    y, x = np.ogrid[-center_y:grid_edge_length - center_y, -center_x:grid_edge_length - center_x]
    mask = x * x + y * y <= radius * radius
    return mask


def max_inside_circle(image, radius_meters, meters_per_pixel):
    mask = circle_mask(image.shape[0] // 2, image.shape[1] // 2, radius_meters / meters_per_pixel, image.shape[0])
    max_intensity = image[mask].max()
    return max_intensity


if __name__ == '__main__':
    main()
