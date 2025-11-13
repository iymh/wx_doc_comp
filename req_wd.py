# LOG
import logging
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
logger = logging.getLogger("LOG")

# env
import os
from dotenv import load_dotenv
load_dotenv()

# ibm-watson
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

wd_key = os.getenv("WD_KEY", None) 
wd_url = os.getenv("WD_URL", None)
prj_id = os.getenv("WD_PRJID", None)

authenticator = IAMAuthenticator(wd_key)
discovery = DiscoveryV2(
    version='2023-03-31',
    authenticator=authenticator
)
discovery.set_service_url(wd_url)

# prjs = discovery.list_projects().get_result()
# prj_ids = prjs['projects']
# print(f'ProjectID: {prj_ids}')

def call_getcollections():
    logger.info(f"call_getcollections")

    ret = discovery.list_collections(
        project_id=prj_id
    ).get_result()
    logger.info(ret)

    return ret

def call_wdsearch(params):
    logger.info(f"call_wdsearch: { params }")

    ret = discovery.query(
        project_id = prj_id,
        collection_ids = params["collection_ids"],
        count = params["count"],
        natural_language_query = params["natural_language_query"]
    ).get_result()
    logger.info(ret)

    return ret

def call_wdautocomp(params):
    logger.info(f"call_wdautocomp: { params }")

    ret = discovery.get_autocompletion(
        project_id = prj_id,
        prefix = params["prefix"],
        count = params["count"]
    ).get_result()
    logger.info(ret)

    return ret
