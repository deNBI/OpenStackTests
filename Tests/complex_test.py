from openstack import connection
import sys
import paramiko
import yaml
import logging
import subprocess
import time,os


def cleanup(conn, floating_ip=None, subnet_id=None):
    logger.info("Starting cleanup...")
    remove_floating_ip(conn, floating_ip)
    delete_server(conn)
    delete_keypair(conn)
    delete_router(conn, subnet_id=subnet_id)
    delete_network(conn)
    logger.info("Cleanup done...")


def delete_router(conn, subnet_id):
    logger.info("Deleting Router..")
    router = conn.network.find_router(ROUTER_NAME)
    if router is None:
        return
    if subnet_id is not None:
        conn.network.remove_interface_from_router(router, subnet_id=subnet_id)
    conn.network.delete_router(router)
    logger.info("Router deleted...")


def delete_network(conn):
    logger.info("Deleting Network..")
    network = conn.network.find_network(NETWORK_NAME)
    if network is None:
        return
    network = conn.network.get_network(network)
    for subnet in network.subnet_ids:
        conn.network.delete_subnet(subnet)
    conn.network.delete_network(network)
    logger.info("Network deleted..")


def remove_floating_ip(conn, floating_ip):
    logger.info("Remove floating ip from server")
    server = conn.compute.find_server(INSTANCE_NAME)

    if server is None or floating_ip is None:
        return
    try:
        conn.compute.remove_floating_ip_from_server(server, floating_ip)
        logger.info("Floating ip removed")
    except Exception:
        pass


def delete_server(conn):
    logger.info("Delete Server ")
    server = conn.compute.find_server(INSTANCE_NAME)

    if server is None:
        return
    conn.compute.delete_server(server)
    logger.info("Server deleted ")


def stop_server(conn):
    logger.info("Stop Server... ")
    server = conn.compute.find_server(INSTANCE_NAME)

    if server is None:
        return
    conn.compute.suspend_server(server)
    conn.compute.wait_for_server(server, status='SUSPENDED')
    logger.info("Stopped Server... ")


def create_network(conn):
    logger.info("Creating Network..")


    network = conn.network.create_network(name=NETWORK_NAME)
    network_subnet = conn.network.create_subnet(name=SUBNETWORK_NAME, network_id=network.id, ip_version=4,
                                                        cidr=SUBNETWORK_CIDR, gateway=SUBNETWORK_GATEWAY)
    logger.info("Network created..")
    return network_subnet.id





def create_router(conn, subnet_id):
    logger.info("Creating Router..")
    body = dict({"network_id": EXTERNAL_GATEWAY_NETWORK_ID})

    router = conn.network.create_router(name=ROUTER_NAME, external_gateway_info=body)

    conn.network.add_interface_to_router(router, subnet_id=subnet_id)
    logger.info("Router created..")

def create_keypair(conn):

        key=paramiko.RSAKey.generate(1024)
        key.write_private_key_file(PRIVATE_KEY_FILE)
        public_key="ssh-rsa {0}".format(key.get_base64())
        keypair = conn.compute.find_keypair(PUBLIC_KEY_NAME)
        if not keypair:
            logger.info("Create Keypair")
            keypair = conn.compute.create_keypair(name=PUBLIC_KEY_NAME ,public_key=public_key)
            return keypair
        elif keypair.public_key != public_key:
            logger.info("Key has changed. Replace old Key")
            conn.compute.delete_keypair(keypair)
            keypair = conn.compute.create_keypair(name=PUBLIC_KEY_NAME, public_key=public_key)
            return keypair
        return keypair

def delete_keypair(conn):
    logger.info("Deleting Private_Key_File from tmp...")
    try:
        os.remove(PRIVATE_KEY_FILE)
    except Exception:
        pass
    logger.info("Private_Key-File deleted from tmp...")
    logger.info("Delete Keypair from Openstack...")
    keypair=conn.compute.find_keypair(PUBLIC_KEY_NAME)
    if not keypair:
        logger.info("No Keypair to delete")
    else:
        conn.compute.delete_keypair(keypair)
        logger.info("Deleted Keypair from Openstack...")




def start_server(conn, subnet_id):
    logger.info("Start Server ")

    image = conn.compute.find_image(DEFAULT_IMAGE)
    if image is None:
        logger.error("Image {0}  not found".format(image))
        print(("Image {0}  not found".format(image)))
        cleanup(conn, subnet_id=subnet_id)
        sys.exit(2)
    flavor = conn.compute.find_flavor(DEFAULT_FLAVOR)
    if flavor is None:
        print("Flavor {0} not found".format(flavor))
        logger.error("Flavor {0} not found".format(flavor))
        cleanup(conn, subnet_id=subnet_id)
        sys.exit(2)
    network = conn.network.find_network(NETWORK_NAME)
    if network is None:
        logger.error("Network {0} not found".format(network))
        print("Network {0} not found".format(network))
        cleanup(conn, subnet_id=subnet_id)
        sys.exit(2)

    server = conn.compute.create_server(
        name=INSTANCE_NAME, image_id=image.id, flavor_id=flavor.id,
        networks=[{"uuid": network.id}],key_name=PUBLIC_KEY_NAME)

    conn.compute.wait_for_server(server)

    logger.info("Server started..")


def add_floating_ip_to_server(conn, subnet_id):
    logger.info("Adding floating ip to server...")

    server = conn.compute.find_server(INSTANCE_NAME)
    if server is None:
        logger.error("Instance {0} not found".format(INSTANCE_NAME))
        print("Instance {0} not found".format(INSTANCE_NAME))
        cleanup(conn, subnet_id=subnet_id)
        sys.exit(2)
    server = conn.compute.get_server(server)
    logger.info("Checking if unused Floating-Ip exist")
    for floating_ip in conn.network.ips():
        if not floating_ip.fixed_ip_address:
            conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)
            logger.info("Adding existing Floating IP  {0} to {1}".format(floating_ip.floating_ip_address,INSTANCE_NAME))
            return str(floating_ip.floating_ip_address)

    networkID = conn.network.find_network(FLOATING_IP_NETWORK)
    if networkID is None:
        logger.error("Network {0} not found".format(FLOATING_IP_NETWORK))
        print("Network {0} not found".format(FLOATING_IP_NETWORK))
        cleanup(conn, subnet_id=subnet_id)
        sys.exit(2)
    networkID = networkID.to_dict()['id']
    floating_ip = conn.network.create_ip(floating_network_id=networkID)
    floating_ip = conn.network.get_ip(floating_ip)
    conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)
    return floating_ip


def connect_ssh_check_google(floating_ip):
    logger.info("Removing IP from known hosts..")
    subprocess.call(['ssh-keygen -R {0}'.format(floating_ip)],shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    logger.info("Trying to connect with SSH to the machine")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(floating_ip, username=DEFAULT_USER, password=CIRROS_PASSWORD, key_filename=PRIVATE_KEY_FILE)
    logger.info("Setting http_proxy...")
    logger.info("Trying to wget -q http://www.google.de/")
    stdin, stdout, stdrr = ssh.exec_command('export http_proxy=http://proxy.cebitec.uni-bielefeld.de:3128; wget -q http://www.google.de/; echo $?;',get_pty=True)
    response = stdout.readlines()[0].replace("\r\n","")
    if (response == '0'):
        logger.info("Connection to Google sucessfull..")
    else:
        logger.error("Google test failed and wget returned " + response)
        print("Google test failed and wget returned " + response)
        cleanup(conn,floating_ip,subnet_id)
        sys.exit(2)





# The Test starts here
try:
    #Reading config variables
    with open('config.yml', 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        LOGFILE = cfg['logfile']
        USERNAME = cfg['authentication']['os_username']
        PASSWORD = cfg['authentication']['os_password']
        PROJECT_NAME = cfg['authentication']['os_project_name']
        USER_DOMAIN_NAME = cfg['authentication']['os_user_domain_name']
        AUTH_URL = cfg['authentication']['os_auth_url']
        PROJECT_DOMAIN_NAME = cfg['authentication']['os_project_domain_name']
        PRIVATE_KEY_FILE='/tmp/private_test_key'
    with open('complex_test.yml', 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        NETWORK_NAME = cfg['network_name']
        SUBNETWORK_NAME = cfg['subnetwork_name']
        INSTANCE_NAME = cfg['instance_name']
        SUBNETWORK_CIDR = cfg['subnetwork_cidr']
        SUBNETWORK_GATEWAY = cfg['subnetwork_gateway']
        ROUTER_NAME = cfg['router_name']
        EXTERNAL_GATEWAY_NETWORK_ID = cfg['external_gateway_network_id']
        DEFAULT_IMAGE = cfg['default_image']
        FLOATING_IP_NETWORK = cfg['floating_ip_network']
        DEFAULT_FLAVOR = cfg['default_flavor']
        DEFAULT_USER = cfg['default_user']
        PUBLIC_KEY_NAME=cfg['public_key_name']
        CIRROS_PASSWORD = cfg['cirros_password']


except Exception as e:
    print("Config error: " + str(e)[:90])
    sys.exit(2)
#setting up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(LOGFILE)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - - %(levelname)s  - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.info("-----------")
logger.info("Started complex test...")
try:
    logger.info("Trying to authenticate at Keystone...  ")
    conn = connection.Connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                 project_name=PROJECT_NAME,
                                 user_domain_name=USER_DOMAIN_NAME, project_domain_name=PROJECT_DOMAIN_NAME)
    logger.info("Session created...  ")
    floating_IP=None
    subnet_id=None
    subnet_id = create_network(conn)


    create_router(conn, subnet_id=subnet_id)
    create_keypair(conn)
    start_server(conn, subnet_id=subnet_id)
    floating_IP = add_floating_ip_to_server(conn, subnet_id=subnet_id)
    time.sleep(60)
    connect_ssh_check_google(floating_ip=floating_IP)
    cleanup(conn, subnet_id=subnet_id, floating_ip=floating_IP)
    logger.info("Succesfull complex test..")
    logger.info("-----------")
    sys.exit(0)
except Exception as e:
    logger.error(e,exc_info=True)
    cleanup(conn, subnet_id=subnet_id, floating_ip=floating_IP)
    logger.info("Failed complex test")
    logger.info("-----------")
    print(str(e)[:150])
    sys.exit(2)
