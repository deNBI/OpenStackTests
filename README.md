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

1. check_cinder.py -> checks if Cinder EndPoint  is avaiable
2. check cinderv2.py -> checks if Cinderv2 EndPoint  is avaiable
3. check_glance.py -> checks if  Glance EndPoint  is avaiable
4. check_keystone.py -> checks if Keystone EndPoint  is avaiable
5. check_neutron.py -> checks if Neutron EndPoint  is avaiable
6. check_swift.py -> checks if Swift EndPoint  is avaiable
7. check_nova.py -> checks if Nova EndPoint  is avaiable
8. create_and_delete_image.py -> Downloads an cirros Image and uploads it a the Openstack-Project, than deletes it

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



