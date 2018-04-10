# OpenStackTests
This repositroy contains some Openstack tests. <br>
## Configuration
You need to install the requirements.
~~~bash
$> pip install -r requirements.txt
~~~
or with pip.
~~~bash
$> pip install git+https://github.com/deNBI/OpenStackTests@master
~~~

or

~~~bash
$> pip install git+https://github.com/deNBI/OpenStackTests@dev
~~~
Before you can start the tests, you need to set some configurations. <br>
You need to set them on the config.yml for all tests and also for the complex test in the complex_test.yml

## Basic-Test
There are some basic tests:

1. endpoint_test.py -> it will test if an endpoint is avaiable just use the name of a service as a param like

    => python3 endpoint_test.py swift
2. create_and_delete_image.py -> Downloads an cirros Image and uploads it a the Openstack-Project, than deletes it

## Complex-Test
The complex test needs beside the config.yml  also the complex_test.yml <br>
The complex Test complex_test.py follows the following Steps:

1. Creates a network,subnet and a router connected to a specific network
2. Start an instance using the default image(cirros)
3. Assign a floating ip to the instance
4. Login into the instance and try connect to google
5. Logout
6. Stop and Delete the Instance
7. Delete network, subnet and route



