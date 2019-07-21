import sys
import time
import logging

import toml
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
from requests import ConnectionError
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Some Global Variables
CONF_FILE = 'config.toml'
CONF = dict()
LOCAL_DB = None
CLOUD_DB = None

def read_config_file(conf_file):
    """Function to read the TOML configuration File and return the config dict"""
    with open(conf_file) as toml_file:
        _conf = toml.load(toml_file)
    return _conf

def connected_to_cloud():
    """Function to check connectivity to the cloud instance. If not connected, retry
       after every 30 seconds
    """
    cloud_connected = False
    while not cloud_connected:
        try:
            cloud_version = CLOUD_DB.ping()
            logger.info('Cloud Version: v{}'.format(cloud_version))
            cloud_connected = True
            return cloud_connected
        except ConnectionError as e:
            logger.info('Cannot connect to Cloud Instance')
            logger.error(e)
            logger.info('Trying again after 30 seconds')
            time.sleep(30.0)

def upload_data(batch_data):
    logger.info('Sending Batch to Cloud')
    if connected_to_cloud():
        try:
            if CLOUD_DB.write_points(batch_data, time_precision='ms'):
                logger.info('Upload Successful')

                logger.info('Updating Local Database with field `status=1`')
                for point in batch_data:
                    for field in point['fields']:
                        point['fields'][field] = float(point['fields'][field])
                    point['fields']['status'] = float(1)
                
                if LOCAL_DB.write_points(batch_data, time_precision='ms'):
                    logger.info('Local DB Updated')
        except Exception as e:
            CLOUD_DB.close()
            LOCAL_DB.close()
            raise(e)


def get_points(conf):
    """
    Query Local Database for data points and format them before uploading
    the batch
    """
    logger.info('Get Data Points for the following Configuration: ')
    logger.info(conf)
    #Create the string using dictionary
    dict_str = ''.join('"{}"=\'{}\''.format(key,value) for key, value in conf['tags'].items())
    QUERY = 'SELECT "{}" FROM "{}" WHERE "status"=0 AND {} LIMIT {}'.format(
                '","'.join(conf['fields']),
                conf['measurement'],
                dict_str,
                conf['limit']
            )
    logger.info('Query: ' + QUERY)
    try:
        query_results = LOCAL_DB.query(QUERY, epoch='ms')
    except InfluxDBClientError as e:
        LOCAL_DB.close()
        CLOUD_DB.close()
        raise(e)
    if len(list(query_results)) == 0:
        logger.info('No Results for the Query')
    else:
        # format the data for the upload
        batch = []
        for point in list(query_results)[0]:
            # standard dict as needed by `influxdb-python`
            # module to write to InfluxDB via HTTP
            upload_json_body = {
                'measurement': conf['measurement'],
                'fields': {}
            }

            if 'tags' in conf:
                upload_json_body['tags'] = conf['tags']
            upload_json_body['time'] = point['time']
            # remove `time` key from the results dict to get all the fields
            del point['time']
            upload_json_body['fields'] = point
            batch.append(upload_json_body)
        logger.debug(batch)
        logger.debug('Current batch length: {}'.format(len(batch))) # should be same as `limit`

        upload_data(batch)


def main():
    """
    main function for uploader
    """
    global CONF, CLOUD_DB, LOCAL_DB
    logger.info('Reading Configuration File')
    CONF = read_config_file(CONF_FILE)

    # DB Configurations
    local_hostname = CONF['local']['host']
    local_port = CONF['local']['port']
    local_db_name = CONF['local']['database']
    logger.info('Local DB Parameter: host:{}, port: {}, db:{}'.format(local_hostname,local_port, local_db_name))
    
    LOCAL_DB = InfluxDBClient(host=local_hostname, port=local_port, database=local_db_name)

    cloud_hostname = CONF['cloud']['endpoint']
    cloud_port = CONF['cloud']['port']
    cloud_db_name = CONF['cloud']['database']
    if CONF['cloud']['secure']:
        cloud_username = CONF['cloud']['username']
        cloud_password = CONF['cloud']['password']
        CLOUD_DB = InfluxDBClient(host=cloud_hostname,
                port=cloud_port,
                ssl=True,
                verify_ssl=False,
                username=cloud_username,
                password=cloud_password,
                database=cloud_db_name)
    else:
        CLOUD_DB = InfluxDBClient(host=cloud_hostname, port=cloud_port, database=cloud_db_name)

    logger.info('Cloud DB Parameter: host:{}, port: {}, db:{}'.format(cloud_hostname, cloud_port, cloud_db_name))

    logger.info('Estabilish connection to Local Instance')
    try:
        ping_local = LOCAL_DB.ping()
        logger.info('Local Version: v{}'.format(ping_local))
    except ConnectionError as e:
        logger.error('Cannot Connect to Local Instance')
        LOCAL_DB.close()
        CLOUD_DB.close()
        raise(e)
    
    if connected_to_cloud():
        try:
            while True:
                for config in CONF.keys():
                    # use the sources and not the DB configuration
                    if config != 'local' and config != 'cloud':
                        get_points(CONF[config])
                        time.sleep(5.0)
        except Exception as e:
            LOCAL_DB.close()
            CLOUD_DB.close()
            raise(e)
        except KeyboardInterrupt:
            LOCAL_DB.close()
            CLOUD_DB.close()
            sys.exit(0)




if __name__ == "__main__":
    main()

    


