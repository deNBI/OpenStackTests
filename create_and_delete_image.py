from openstack import connection
import sys, os
from glanceclient import Client
import logging,requests
import yaml
VERSION=2
try:
    with open('config.yml','r') as ymlfile:
        cfg=yaml.load(ymlfile)
        LOGFILE=cfg['logfile']
        USERNAME=cfg['authentication']['os_username']
        PASSWORD=cfg['authentication']['os_password']
        PROJECT_NAME=cfg['authentication']['os_project_name']
        USER_DOMAIN_NAME=cfg['authentication']['os_user_domain_name']
        AUTH_URL=cfg['authentication']['os_auth_url']
        PROJECt_DOMAIN_NAME=cfg['authentication']['os_project_domain_name']
        CINDER_ENDPOINTv2=cfg['endpoints']['cinderv2_endpoint']
        IMAGE_FILE=cfg['image']['image_tmp_file']
        IMAGE_URL=cfg['image']['image_download_url']

except Exception as e:
    print("Config error: " +  str(e)[:90])
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
    logger.info("Downloading Cirros image..")
    r=requests.get(IMAGE_URL,stream=True)
    with open(IMAGE_FILE ,"wb") as f:
        f.write(r.content)
    logger.info("Trying to authenticate at Keystone...  ")
    conn = connection.Connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                 project_name=PROJECT_NAME,
                                 user_domain_name=USER_DOMAIN_NAME, project_domain_name='default')
    logger.info("Session created...  ")

    glance = Client(VERSION, session=conn.session)
    logger.info("Glance client connected..")

    logger.info("Creating Image....")
    image = glance.images.create(name="CirrosTest", disk_format="qcow2", container_format="bare")
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
    sys.exit(0)
except Exception as e:
    os.remove(IMAGE_FILE)
    logger.error(str(e))
    print(str(e)[:100])
    sys.exit(2)


