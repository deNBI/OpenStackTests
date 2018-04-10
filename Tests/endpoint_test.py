from openstack import connection
import yaml, logging, sys
import requests
try:
    with open('config.yml', 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        LOGFILE = cfg['logfile']
        USERNAME = cfg['authentication']['os_username']
        PASSWORD = cfg['authentication']['os_password']
        AUTH_URL = cfg['authentication']['os_auth_url']
        PROJECT_NAME=cfg['authentication']['os_project_name']
        USER_DOMAIN_NAME=cfg['authentication']['os_user_domain_name']
        PROJECT_DOMAIN_NAME=cfg['authentication']['os_project_domain_name']
        SERVICE=sys.argv[1]


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

try:
    logger.info("----------------------")
    logger.info("Start Test: check_{0}".format(SERVICE))
    logger.info("Trying to connect to Keystone-Endpoint... ")

    conn = connection.Connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                 project_name=PROJECT_NAME,
                                 user_domain_name=USER_DOMAIN_NAME, project_domain_name=PROJECT_DOMAIN_NAME)
    if SERVICE == '--help':
        print('To test an endpoint you need to give the service name as the first parameter \n'
              'For example: python3 endpoint_test.py swift \n'
              'This would test the swift service.\n' )
        print('Avaiable Services are : ')
        for serv in conn.identity.services():
            print(serv.to_dict()['name'])
        sys.exit(0)
    token = conn.authorize()

    serviceid = conn.identity.find_service(SERVICE).to_dict()['id']
    for e in conn.identity.endpoints():
        e = e.to_dict()
        if e['service_id'] == serviceid and e['interface'] == 'public':
            url=e['url']
            if SERVICE == 'cinder' or SERVICE =='cinderv2' or SERVICE == 'nova':
                url=url.split('%')[0]

    headers={"X-Auth-Token" : token}
    r = requests.get(url,headers=headers)
    if (str(r.status_code)[0] == '2' or SERVICE == 'glance' and str(r.status_code)[0] == '3'):
        logger.info("{0} alive ...".format(SERVICE))
        logger.info("Succesful Test: check_{0}".format(SERVICE))
        logger.info("----------------------")
        sys.exit(0)
    else :
        logger.error(str(r.status_code) + ": " + str(r.content)[:97])
        logger.info("Failed Test: check_{0}".format(SERVICE))
        logger.info("----------------------")
        print(str(r.status_code) + ": " + str(r.content))
        sys.exit(2)




except Exception as e:
    logger.error(str(e))
    logger.info("Failed Test: check_{0}".format(SERVICE))
    logger.info("----------------------")
    print(str(e)[:100])
    sys.exit(2)
