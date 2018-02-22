from openstack import connection
import sys, os
from glanceclient import Client
import logging, requests
from keystoneauth1.identity import v3
from keystoneauth1 import session


import yaml

VERSION = 2
try:
    with open('config.yml', 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        LOGFILE = cfg['logfile']
        USERNAME = cfg['authentication']['os_username']
        PASSWORD = cfg['authentication']['os_password']
        USER_DOMAIN_ID = cfg['authentication']['os_user_domain_id']
        AUTH_URL = cfg['authentication']['os_auth_url']
        PROJECT_DOMAIN_ID = cfg['authentication']['os_project_domain_id']
        IMAGE_FILE =cfg['image']['image_tmp_file']
        IMAGE_URL = cfg['image']['image_download_url']

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


def deleting_image():
    logger.info("Deleting Image from tmp...")
    os.remove(IMAGE_FILE)
    logger.info("Image deleted from tmp...")
    logger.info("Deleting Image from Openstack...")
    glance.images.delete(image.id)
    logger.info("Image deleted from openstack......")


try:

    logger.info("----------------------")
    logger.info("Start Test: create_and_delete_image")
    logger.info("Downloading Cirros image..")
    r = requests.get(IMAGE_URL, stream=True)
    with open(IMAGE_FILE, "wb") as f:
        f.write(r.content)
    logger.info("Trying to authenticate at Keystone...  ")

    auth=v3.Password(
        auth_url=AUTH_URL,
        username=USERNAME,
        password=PASSWORD,
        user_domain_id=USER_DOMAIN_ID,
        project_domain_id=PROJECT_DOMAIN_ID)
    session=session.Session(auth=auth)


    glance = Client(VERSION, session=session)
    logger.info("Glance client connected..")

    logger.info("Creating Image....")
    image = glance.images.create(name="CirrosTest",disk_format='qcow2',container_format='bare')
    logger.info("Uploading Image...")
    glance.images.upload(image.id, open(IMAGE_FILE, 'rb'))

    image_status = glance.images.get(image.id)['status']
    if (image_status == 'killed' or image_status == 'deleted'):
        logger.error("Image couldn't be properly uploaded")
        print("Image couldn't be properly uploaded")
        deleting_image()
        sys.exit(2)

    logger.info("Image active...")

    deleting_image()
    logger.info("Succesfull test create_and_delete_image")
    logger.info("----------------------")
    sys.exit(0)
except Exception as e:
    os.remove(IMAGE_FILE)

    logger.error(str(e))
    logger.info("Failed test create_and_delete_image")
    logger.info("----------------------")
    print(str(e)[:100])
    sys.exit(2)
