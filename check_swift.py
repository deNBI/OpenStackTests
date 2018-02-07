 
from openstack import connection
import sys, os
import requests
import yaml
import logging

try:
    with open('config.yml','r') as ymlfile:
        cfg=yaml.load(ymlfile)
        LOGFILE=cfg['logfile']
        USERNAME=cfg['authentication']['os_username']
        PASSWORD=cfg['authentication']['os_password']
        PROJECT_NAME=cfg['authentication']['os_project_name']
        USER_DOMAIN_NAME=cfg['authentication']['os_user_domain_name']
        AUTH_URL=cfg['authentication']['os_auth_url']
        PROJECT_DOMAIN_NAME=cfg['authentication']['os_project_domain_name']
        SWIFT_ENDPOINT=cfg['endpoints']['swift_endpoint']
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


try:
    logger.info("----------------------")
    logger.info("Start Test: check_switf")
    logger.info("Trying to connect to Swift-Endpoint... ")
    conn = connection.Connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                 project_name=PROJECT_NAME,
                                 user_domain_name=USER_DOMAIN_NAME, project_domain_name=PROJECT_DOMAIN_NAME)
    token=conn.authorize()
    headers={"X-Auth-Token" : token}
    r = requests.get(SWIFT_ENDPOINT,headers=headers)
    if (str(r.status_code)[0] == '2'):
        logger.info("Swift alive ...")
        logger.info("Succesful Test: check_swift")
        logger.info("----------------------")
        sys.exit(0)
    else :
        logger.error(str(r.status_code) + ": " + str(r.content)[:97])
        logger.info("Failed Test: check_swift")
        logger.info("----------------------")
        print(str(r.status_code) + ": " + str(r.content))
        sys.exit(2)
except Exception as e :
    logger.error(str(e))
    logger.info("Failed Test: check_swift")
    logger.info("----------------------")
    print(str(e)[:100])
    sys.exit(2)