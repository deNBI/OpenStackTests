from openstack import connection
import sys, os

import yaml
import logging
from pexpect import pxssh


def delete_router(conn,subnet_id):
    logger.info("Deleting Router..")
    router=conn.network.find_router(ROUTER_NAME)
    if router is None:
        return
    conn.network.remove_interface_from_router(router,subnet_id=subnet_id)
    conn.network.delete_router(router)
    logger.info("Router deleted...")
def delete_network(conn):
    logger.info("Deleting Network..")
    network = conn.network.find_network(NETWORK_NAME)
    if network is None:
        return
    network = conn.network.get_network(network)
    for subnet in network.subnet_ids:
        conn.network.delete_subnet(subnet, ignore_missing=True)
    conn.network.delete_network(network, ignore_missing=True)
    logger.info("Network deleted..")


def create_network(conn):
    logger.info("Creating Network..")
    try:
        network = conn.network.create_network(name=NETWORK_NAME)
        network_subnet = conn.network.create_subnet(name=SUBNETWORK_NAME, network_id=network.id, ip_version=4,
                                                    cidr=SUBNETWORK_CIDR ,gateway=SUBNETWORK_GATEWAY)
        logger.info("Network created..")
        return network_subnet.id
    except Exception as e:
        logger.error(str(e))
        print(str(e)[:100])
        delete_network(conn)
        sys.exit(2)



def create_router(conn, subnet_id):
    logger.info("Creating Router..")
    body = dict({"network_id": EXTERNAL_GATEWAY_NETWORK_ID})
    try:
        router = conn.network.create_router(name=ROUTER_NAME, external_gateway_info=body)

        conn.network.add_interface_to_router(router, subnet_id=subnet_id)
        logger.info("Router created..")
    except Exception as e:
        logger.error(str(e))
        print(str(e)[:100])
        delete_router(conn,subnet_id=subnet_id)
        delete_network(conn)
        sys.exit(2)


def start_server(conn,subnet_id):
    logger.info("Start Server ")
    try:
        image = conn.compute.find_image(DEFAULT_IMAGE)
        if image is None:
            logger.error("Image " + str(image) + " not found")
            print(("Image " + str(image) + " not found"))
            delete_router(conn, subnet_id=subnet_id)
            delete_network(conn)
            sys.exit(2)
        flavor = conn.compute.find_flavor(DEFAULT_FLAVOR)
        if flavor is None:
            print("Flavor" + str(flavor) + " not found")
            logger.error("Flavor " + str(flavor) + " not found")
            delete_router(conn, subnet_id=subnet_id)
            delete_network(conn)
            sys.exit(2)
        network = conn.network.find_network(NETWORK_NAME)
        if network is None:
            logger.error("Network " + str(network) + " not found")
            print("Network " + str(network) + " not found")
            delete_router(conn, subnet_id=subnet_id)
            delete_network(conn)
            sys.exit(2)

        server = conn.compute.create_server(
            name=INSTANCE_NAME, image_id=image.id, flavor_id=flavor.id,
            networks=[{"uuid": network.id}], )

        conn.compute.wait_for_server(server)

        logger.info("Server started..")

    except Exception as e:
        logger.error(str(e))
        print(str(e)[:100])
        delete_server(conn)
        delete_router(conn, subnet_id=subnet_id)
        delete_network(conn)
        sys.exit(2)


def add_floating_ip_to_server(conn,subnet_id):
    logger.info("Adding floating ip to server...")
    try:
        server = conn.compute.find_server(INSTANCE_NAME)
        if server is None:
            logger.error("Instance " + INSTANCE_NAME + "not found")
            print("Instance " + INSTANCE_NAME + "not found")
            delete_server(conn)
            delete_router(conn, subnet_id=subnet_id)
            delete_network(conn)
            sys.exit(2)
        server = conn.compute.get_server(server)
        logger.info("Checking if unused Floating-Ip exist")
        for floating_ip in conn.network.ips():
            if not floating_ip.fixed_ip_address:
                conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)
                logger.info("Adding existing Floating IP " + str(floating_ip.floating_ip_address) + "to  " + INSTANCE_NAME)
                return str(floating_ip.floating_ip_address)

        networkID = conn.network.find_network(FLOATING_IP_NETWORK)
        if networkID is None:
            logger.error("Network " + FLOATING_IP_NETWORK + " not found")
            print("Network " + FLOATING_IP_NETWORK + " not found")
            delete_server(conn)
            delete_router(conn, subnet_id=subnet_id)
            delete_network(conn)
            sys.exit(2)
        networkID = networkID.to_dict()['id']
        floating_ip = conn.network.create_ip(floating_network_id=networkID)
        floating_ip = conn.network.get_ip(floating_ip)
        conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)
        return floating_ip
    except Exception as e:
        logger.error(str(e))
        print(str(e)[:100])
        remove_floating_ip(conn,floating_ip)
        delete_server(conn)
        delete_router(conn, subnet_id=subnet_id)
        delete_network(conn)
        sys.exit(2)
def remove_floating_ip(conn,floating_ip):
    logger.info("Remove floating ip from server")
    server = conn.compute.find_server(INSTANCE_NAME)

    if server is None:
        logger.error("Instance " + INSTANCE_NAME + "not found")
        return
    try:
        conn.compute.remove_floating_ip_from_server(server,floating_ip)
        logger.info("Floating ip removed")
    except Exception:
        pass
def delete_server(conn):
    logger.info("Delete Server " )
    server=conn.compute.find_server(INSTANCE_NAME)

    if server is None:
        logger.error("Instance " + INSTANCE_NAME +"not found")
        return
    conn.compute.delete_server(server)
    logger.info("Server deleted ")




def stop_server(conn):
    logger.info("Stop Server... ")
    server = conn.compute.find_server(INSTANCE_NAME)

    if server is None:
        logger.error("Instance " + INSTANCE_NAME + "not found")
        return
    conn.compute.suspend_server(server)
    conn.compute.wait_for_server(server,status='SUSPENDED')
    logger.info("Stopped Server... ")



def connect_ssh_check_google(floating_ip):
    s=pxssh.pxssh()
    if not s.login(floating_ip,'cirros','cubswin:)'):
        print("SSH failed")
        print(str(s))
    else:
        print("SSsh succesfull")
        s.sendline('touch test.txt')
        s.prompt()
        print(s.before)
        s.logout()





try:
    with open('config.yml', 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        LOGFILE = cfg['logfile']
        USERNAME = cfg['authentication']['os_username']
        PASSWORD = cfg['authentication']['os_password']
        PROJECT_NAME = cfg['authentication']['os_project_name']
        USER_DOMAIN_NAME = cfg['authentication']['os_user_domain_name']
        AUTH_URL = cfg['authentication']['os_auth_url']
        PROJECT_DOMAIN_NAME = cfg['authentication']['os_project_domain_name']
    with open('create_network_subnet_router.yml', 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        NETWORK_NAME=cfg['network_name']
        SUBNETWORK_NAME=cfg['subnetwork_name']
        INSTANCE_NAME=cfg['instance_name']
        SUBNETWORK_CIDR=cfg['subnetwork_cidr']
        SUBNETWORK_GATEWAY=cfg['subnetwork_gateway']
        ROUTER_NAME=cfg['router_name']
        EXTERNAL_GATEWAY_NETWORK_ID=cfg['external_gateway_network_id']
        DEFAULT_IMAGE=cfg['default_image']
        FLOATING_IP_NETWORK=cfg['floating_ip_network']
        DEFAULT_FLAVOR=cfg['default_flavor']
except Exception as e:
    print("Config error: " + str(e)[:90])
    sys.exit(2)

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

    subnet_id = create_network(conn)
    create_router(conn, subnet_id=subnet_id)
    start_server(conn,subnet_id=subnet_id)
    floating_IP=add_floating_ip_to_server(conn,subnet_id=subnet_id)
    print(floating_IP)
    #connect_ssh_check_google(floating_ip=floating_IP)
    remove_floating_ip(conn,floating_IP)
    stop_server(conn)
    delete_server(conn)
    delete_router(conn, subnet_id=subnet_id)
    delete_network(conn)
    logger.info("Succesfull complex test..")
    logger.info("-----------")
    sys.exit(0)
except Exception as e:
    logger.error(str(e))
    print(str(e)[:100])
    sys.exit(2)
