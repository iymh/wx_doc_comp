import asyncio
# user modules
import req_wxai as GEN
import req_wml as SPM

# LOG
import logging
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
logger = logging.getLogger("LOG")

# env
# from dotenv import load_dotenv
# load_dotenv()

C_RED = '\033[31m'
C_RST = '\033[0m'
# logger.info(f"{C_RED}　no: {no}{C_RST}")

# server init
def start():
    # GEN.call_genai({"prompt": "IBM Watsonとはなんですか？"})
    # asyncio.run(VDB.add_vdb(["Hello", "world"]))
    iam_token = SPM.get_iam_token()
    print("token:", iam_token)

    input_fields = ["id", "Comments", "Gender", "Reason"]
    values = [
        [1, "Room is good", "male", "business"],
        [2, "Bathroom is bad", "female", "laleisure"]
    ]
    prediction_result = SPM.get_predictions(iam_token, input_fields, values)
    print(prediction_result)


# init from python script
logger.info(f'__name__ = {__name__}')
if __name__ == "__main__":
    start()

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(start())