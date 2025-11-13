from pydantic import BaseModel
import asyncio
from typing import AsyncGenerator

# LOG
import logging
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
logger = logging.getLogger("LOG")

# env
import os
from dotenv import load_dotenv
load_dotenv()

# Langchain
from langchain_core.prompts import PromptTemplate

# ibm-watsonx-ai
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes, DecodingMethods
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames
from langchain_ibm import WatsonxLLM


api_key = os.getenv("API_KEY", None) 
api_url = os.getenv("WML_URL", None)
creds = Credentials(url=api_url, api_key=api_key)
prj_id = os.getenv("WX_PRJID", None)

# print([model.name for model in ModelTypes])
DEFAULT_MODEL = "meta-llama/llama-3-3-70b-instruct"

# Parameters
class Params(BaseModel):
    modelname: str = DEFAULT_MODEL
    prompt: str = ""
    stream: bool = False
    decoding_method: str = "greedy"
    min_new_tokens: int = 10
    max_new_tokens: int = 50
    repetition_penalty: float = 1.1
    # top_k: int = 3
    # temperature: float = 0.05
    # random_seed: int = 1
    stop_sequences: list[str]

def setLlmChain(params:Params):
    prms = {
        GenTextParamsMetaNames.DECODING_METHOD: params.decoding_method if params and hasattr(params,'decoding_method') else DecodingMethods.GREEDY.value,
        GenTextParamsMetaNames.MAX_NEW_TOKENS: params.max_new_tokens if params and hasattr(params,'max_new_tokens') else 100,
        GenTextParamsMetaNames.MIN_NEW_TOKENS: params.min_new_tokens if params and hasattr(params,'min_new_tokens') else 10,
        GenTextParamsMetaNames.TEMPERATURE: params.temperature if params and hasattr(params,'temperature') else 0.5,
        GenTextParamsMetaNames.REPETITION_PENALTY: params.repetition_penalty if params and hasattr(params,'repetition_penalty') else 1.1,
        GenTextParamsMetaNames.TOP_K: params.top_k if params and hasattr(params,'top_k') else 50,
        GenTextParamsMetaNames.TOP_P: params.top_p if params and hasattr(params,'top_p') else 1,
        GenTextParamsMetaNames.STOP_SEQUENCES: params.stop_sequences if params and hasattr(params,'stop_sequences') else []
    }

    llm = WatsonxLLM(
        model_id = params.modelname if params and hasattr(params,'modelname') else DEFAULT_MODEL,
        url = creds["url"],
        apikey = creds["apikey"],
        project_id = prj_id,
        params=prms
    )
    # ret = llm.generate(prompts=[params['prompt']])

    ptemplate = PromptTemplate(
        input_variables=["question"],
        template="日本語で答えてください : {question}",
    )
    lchain = ptemplate | llm
    return lchain

def call_genai(params: Params):
    logger.info(f"call_genai: { params }")

    lchain = setLlmChain(params)
    ret = lchain.invoke({"question":params.prompt})
    logger.info(ret)

    return ret

async def call_genai_stream(params) -> AsyncGenerator[str, None]:
    logger.info(f"call_genai_stream: { params }")

    lchain = setLlmChain(params)
    for chunk in lchain.stream({"question": params.prompt}):
        print (chunk)
        yield chunk
        await asyncio.sleep(0.001)
