# -*- coding: utf-8 -*-

import configparser
import os
import time
import calendar
import logging

import requests
import numpy as np
import scipy.spatial

import wms
import wfs

# Komakallio location in EPSG:3067 coordinates
KOMAKALLIO_EPSG3067 = (355121.064967, 6673513.77179)

# Radar image scale
METERS_PER_PIXEL = 1000.0

# Bounding box edge length in meters
BOUNDING_BOX_SIZE = 300000.0


def main():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    # Configure logger
    log_file = os.path.join(base_dir, 'radarsafety.log')
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(filename=log_file, format='%(asctime)s - %(name)s:%(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Try to read API key from config file
    config_filename = 'config.ini'
    config_path = os.path.join(base_dir, config_filename)
    if not os.path.isfile(config_path):
        logger.error('Config file not found!')
        return
    config = configparser.ConfigParser()
    config.read(config_path)
    try:
        api_key = config['API']['api_key']
    except KeyError:
        logger.error('API key not found in config!')
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
        logger.error('Radar observation time not available!')
        return

    # Fetch radar image
    logger.debug('Fetching radar image for {}'.format(latest_radar_time))
    image = wms.fetch_radar_image(latest_radar_time, api_key, bounding_box, image_edge_length)

    # Check if image returned by server is valid
    if image.mode is not 'I':
        logger.error('Image not available!')
        return

    image.save(os.path.join(base_dir, 'latest_rain_intensity.png'))

    # Calculate maximum rain inside bounding box
    rain_intensity = np.array(image) / 100.0
    max_intensity = rain_intensity.max()
    logger.debug('Maximum rain intensity in bounding box: {} mm/h'.format(max_intensity))

    # Calculate maximum rain intensity inside circles of different radii
    api_data = {}
    for radius_km in [50, 30, 10, 3, 1]:
        radius_m = 1000 * radius_km
        max_intensity_inside_circle = max_inside_circle(rain_intensity, radius_m, METERS_PER_PIXEL)
        logger.debug('Maximum rain intensity inside {} km: {} mm/h'.format(radius_km, max_intensity_inside_circle))
        api_data['{}km'.format(radius_km)] = [max_intensity_inside_circle, 'mm/h']

    rain_distance = closest_rain(rain_intensity, rain_intensity.shape[1] // 2, rain_intensity.shape[0] // 2, METERS_PER_PIXEL)
    if rain_distance is None:
        logger.debug('No rain in sight.')
        api_data['rain_distance'] = [None, 'km']
    else:
        rain_distance_rounded = round(rain_distance, 2)
        logger.debug('Distance to rain: {} km'.format(rain_distance_rounded))
        api_data['rain_distance'] = [rain_distance_rounded, 'km']

    logger.debug('Sending: {}'.format(api_data))
    # Report data to Komakallio API
    try:
        report_to_api(api_data, latest_radar_time)
    except ConnectionError as e:
        logger.error(e)
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
    except requests.exceptions.ConnectionError:
        raise ConnectionError('Could not establish connection to Komakallio API!')
    if report_response.status_code != 200:
        raise ConnectionError('Komakallio API returned status code {}'.format(report_response.status_code))


def iso_string_to_unix_timestamp(iso_string):
    timestamp = calendar.timegm(time.strptime(iso_string, '%Y-%m-%dT%H:%M:%SZ'))
    return timestamp


def circle_mask(center_x, center_y, radius, grid_edge_length):
    y, x = np.ogrid[-center_y:grid_edge_length - center_y, -center_x:grid_edge_length - center_x]
    mask = x * x + y * y <= radius * radius
    return mask


def max_inside_circle(image, radius_meters, meters_per_pixel):
    mask = circle_mask(image.shape[1] // 2, image.shape[0] // 2, radius_meters / meters_per_pixel, image.shape[0])
    max_intensity = image[mask].max()
    return max_intensity


def closest_rain(image, center_x, center_y, meters_per_pixel):
    rain_pixels = np.vstack(np.where(image > 0)).T
    if rain_pixels.size == 0:
        return None
    kdtree = scipy.spatial.KDTree(rain_pixels)
    closest_distances_pixels, index = kdtree.query((center_y, center_x))
    closest_distances_km = meters_per_pixel * closest_distances_pixels / 1000.0
    return closest_distances_km


if __name__ == '__main__':
    main()
