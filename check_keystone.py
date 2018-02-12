
import sys
import requests
import logging
import yaml

try:
    with open('config.yml','r') as ymlfile:
        cfg=yaml.load(ymlfile)
        LOGFILE=cfg['logfile']
        AUTH_URL=cfg['authentication']['os_auth_url']
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
    logger.info("Start Test: check_keystone")
    logger.info("Trying to connect to Keystone-Endpoint... ")
    r=requests.get(AUTH_URL)
    print(r.content)
    if(str(r.status_code)[0] == '2'):
        logger.info("Nova alive ...")
        logger.info("Succesful Test: check_keystone")
        logger.info("----------------------")
        sys.exit(0)
    else:
        logger.error(str(r.status_code) + ": " + str(r.content)[:97])
        logger.info("Failed Test: check_keystone")
        logger.info("----------------------")
        print(str(r.status_code) + ": " + str(r.content))
        sys.exit(2)

except Exception as e:
    logger.error(str(e))
    logger.info("Failed Test: check_nova")
    logger.info("----------------------")
    print(str(e)[:100])
    sys.exit(2)

