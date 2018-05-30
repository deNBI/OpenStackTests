# OpenStackTests
This repositroy contains Openstack tests based python3. <br>
## Configuration
You need to install the requirements.
~~~bash
$> pip3 install -r requirements.txt
~~~
or with pip.
~~~bash
$> pip3 install git+https://github.com/deNBI/OpenStackTests@master
~~~

or

~~~bash
$> pip3 install git+https://github.com/deNBI/OpenStackTests@dev
~~~
Before you can start the tests you have to set some configurations. <br>
All tests require the config.yml. The more complex tests also require the complex_test.yml

## Basic-Test
There are some basic tests:

#### endpoint_test.py 
The endpont_test sends an HTTP OPTIONS request to a specific Url of a service like glance.
If the returning status code is not equal than 5xx, the test was successful
You can see all avaiable services with the command:
    
~~~bash
$> python3 endpoint_test.py --help
~~~
also if you would want to test all avaiable endpoints one after the other you can just use:
    
~~~bash
$> python3 endpoint_test.py
~~~
    
if you want to test one specific endpoint use:
    
~~~bash
$> python3 endpoint_test.py glance
~~~
    
  
#### create_and_delete_image.py 
The create_and_delete_image test goes through the following steps:
    
1. Downloads the actual cirros image
2. Uploads the cirros image
3. Deletes the image
   
If the image was uploaded and deleted without errors the test was succesfull
  

## Complex-Test
The complex test needs beside the config.yml  also the complex_test.yml <br>
The  complex_test.py goes through the following steps::

1. Creates a network,subnet and a router connected to a specific network
2. Start an instance using the default image(cirros)
3. Assign a floating ip to the instance
4. Login into the instance and try connect to google
5. Logout
6. Stop and Delete the Instance
7. Delete network, subnet and route



