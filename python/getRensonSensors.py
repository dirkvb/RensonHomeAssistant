# Script to retrieve the sensors available from the Renson healthbox 3
#    and put them in a yaml config which can be copied to the Home Assistant configuration.yaml
#
# File revisions:
#   1.0, 05-01-2023, Initial version
#
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# dirkvb wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.
# Beerware license by Poul-Henning Kamp
# ----------------------------------------------------------------------------
#

import requests
import yaml
import random

# The yaml-package requires a helper class to properly have indentation in file
#   See https://reorx.com/blog/python-yaml-tips/
class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)


# Main function where I query the url, and loop over rooms and sensors
def main(url):
    # First we just request all the info available
    all_info = requests.get('http://' + url + '/v2/api/data/current')
    all_info = all_info.json()

    sensor_list = []

    # Go over all rooms
    rooms = all_info['room']
    for room in rooms:
        room_info = rooms[room]

        # Retrieve room name once for convenience
        room_name = room_info['name']
        room_name_clean = room_name.lower()
        room_name_clean = room_name_clean.replace(' ', '_')

        # Depending on the room type, we have different sensors
        #     but they are all listed under sensor with the type
        sensors = room_info['sensor']
        for sensor_num in range(len(sensors)):
            # Make a sensor name by combining room name and sensor type
            sensor = sensors[sensor_num]
            sensor_type_name = sensor['type']
            sensor_type_name_clean = sensor_type_name.lower()
            sensor_type_name_clean = sensor_type_name_clean.replace( ' ', '_' )
            sensor_name = room_name + ' ' + sensor_type_name
            sensor_id = room_name_clean + '_' + sensor_type_name_clean

            # Convert sensor type to correct url
            if sensor_type_name == "indoor relative humidity":
                parameter_type = 'humidity'
            elif sensor_type_name == "indoor temperature":
                parameter_type = 'temperature'
            elif sensor_type_name == "indoor air quality index":
                parameter_type = 'index'
            elif sensor_type_name == "indoor CO2" \
                or sensor_type_name == "indoor volatile organic compounds":
                parameter_type = 'concentration'
            else:
                parameter_type = 'error'

            # Get and convert the unit to homeassistant understandable unit
            unit = sensor['parameter'][parameter_type]['unit']
            if unit == 'deg C':
                unit = '°C'
            elif unit == 'pct':
                unit = '%'

            # Compile sensor url
            resource_url = 'http://' + url + '/v2/api/data/current/room/' + str(room) + '/sensor/' + str(sensor_num) + '/parameter/' + parameter_type + '/value'

            # For the update interval, we add a bit of randomness
            #   to make sure the Renson box is not overloaded with requests
            scan_interval = random.randrange(-5, 5) + 30;

            # Store info for this sensor
            sensor_list.append({ 'platform': 'rest',
                                 'name': sensor_name,
                                 'resource': resource_url,
                                 'unit_of_measurement': unit,
                                 'scan_interval': scan_interval,
                                 'unique_id': sensor_id })

    # Dump the yaml, which you should copy in your configuration.yaml
    #   I use a file in the folder where this script is located
    with open('renson_configuration.yaml', 'w') as yaml_file:
        yaml.dump( { 'sensor': sensor_list }, yaml_file, Dumper=IndentDumper, allow_unicode=True)


if __name__ == "__main__":
    main('192.168.1.XX')
