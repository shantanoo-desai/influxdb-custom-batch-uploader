from setuptools import setup

setup(name='uploader',
    version=1.0,
    description='Migrate values from local InfluxDB instance to InfluxDB Server/Cloud',
    url='https://github.com/shantanoo-desai/influxdb-custom-batch-uploader',
    author='Shantanoo Desai',
    author_email='shantanoo.desai@gmail.com',
    license='MIT',
    packages=['uploader'],
    scripts=['bin/uploader'],
    install_requires=[
        'influxdb',
        'toml'
    ],
    include_data_package=True,
    zip_safe=False
)