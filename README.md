# Batch-Uploader-InfluxDB
Script for uploading data to an InfluxDB Cloud/Server and updating your local InfluxDB instance periodically using batch uploads.

Information about the working is documented as follows:

1. [Custom Batch Uploads for InfluxDB without Kapacitor using Python-3.x - Part 1](https://medium.com/@shantanoodesai/custom-batch-uploads-for-influxdb-without-kapacitor-using-python-3-x-part-1-6720381b5ac0)

2. [Custom Batch Uploads fro InfluxDB without Kapacitor using Python-3.x - Part 2](https://medium.com/@shantanoodesai/custom-batch-uploads-for-influxdb-without-kapacitor-using-python-3-x-part-2-70ee87668b3e)


## Usage
Clone the repository and create a `virtualenv` using:

    python -m venv venv

    pip install -e .

Change the values in the `config.toml` accordingly and run code using:

    uploader

## Warnings

> Do not run this script on production servers or live systems!

Please run the script on some sample measurements and make sure everything works well.
If not you will obtain a lot of duplicate data.