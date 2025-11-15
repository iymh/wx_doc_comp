# Module files
import req_wxai as GEN
import req_wd as WDFUNC

# Server
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

# LOG
import logging
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
logger = logging.getLogger("LOG")

app = FastAPI(debug=True)

# Path Routing
@app.post("/gen")
# text invoke
def ibm_genai(params: GEN.Params):
    return GEN.call_genai(params)

# test stream
@app.post("/stream")
async def stream(params: GEN.Params):
    generator = GEN.call_genai_stream(params)
    return StreamingResponse(generator, media_type='text/event-stream')

# WD func
@app.get("/wdcols")
async def wdcols():
    return WDFUNC.call_getcollections()

@app.post("/wdsearch")
async def wdsearch(request: Request):
    data = await request.json()
    natural_language_query = data.get("natural_language_query")
    if natural_language_query is not None:
        return WDFUNC.call_wdsearch(data)
    else:
        return {"error": "invalid params"}

@app.post("/wdautocomp")
async def wdautocomp(request: Request):
    data = await request.json()
    prefix = data.get("prefix")
    if prefix is not None:
        return WDFUNC.call_wdautocomp(data)
    else:
        return {"error": "invalid params"}

@app.post("/wdlistdocuments")
async def wdlistdocuments(request: Request):
    data = await request.json()
    collection_id = data.get("collection_id")
    if collection_id is not None:
        return WDFUNC.call_listdocuments(data)
    else:
        return {"error": "collection_id is required"}

@app.post("/wdadddocument")
async def wdadddocument(request: Request):
    logger.info("wdadddocument エンドポイント呼び出し")
    data = await request.json()
    logger.info(f"リクエストデータ: {data}")
    
    collection_id = data.get("collection_id")
    logger.info(f"collection_id: {collection_id}")
    logger.info(f"file存在: {'file' in data}")
    logger.info(f"filename存在: {'filename' in data}")
    
    if collection_id is not None and ('file' in data or 'filename' in data):
        logger.info("call_adddocument を呼び出します")
        result = WDFUNC.call_adddocument(data)
        logger.info(f"call_adddocument 結果: {result}")
        return result
    else:
        error_msg = "collection_id and either file or filename are required"
        logger.error(f"エラー: {error_msg}")
        return {"error": error_msg}

@app.post("/wdgetdocument")
async def wdgetdocument(request: Request):
    data = await request.json()
    collection_id = data.get("collection_id")
    document_id = data.get("document_id")
    if collection_id is not None and document_id is not None:
        return WDFUNC.call_getdocument(data)
    else:
        return {"error": "collection_id and document_id are required"}

@app.post("/wdupdatedocument")
async def wdupdatedocument(request: Request):
    data = await request.json()
    collection_id = data.get("collection_id")
    document_id = data.get("document_id")
    if collection_id is not None and document_id is not None:
        return WDFUNC.call_updatedocument(data)
    else:
        return {"error": "collection_id and document_id are required"}

@app.post("/wddeletedocument")  # DELETEからPOSTに変更
async def wddeletedocument(request: Request):
    data = await request.json()
    collection_id = data.get("collection_id")
    document_id = data.get("document_id")
    logger.info(f"wddeletedocument エンドポイント呼び出し - collection_id: {collection_id}, document_id: {document_id}")
    
    if collection_id is not None and document_id is not None:
        result = WDFUNC.call_deletedocument(data)
        logger.info(f"削除結果: {result}")
        return result
    else:
        return {"error": "collection_id and document_id are required"}

# mount HTML file for root path
app.mount("/", StaticFiles(directory="public",html=True), name="public")

# server init
def start():
    logger.info('[start]')
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
    # uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

# init from python script
logger.info(f'__name__ = {__name__}')
if __name__ == "__main__":
    start()

# init manual command
# uvicorn main:app --reload
# http://localhost:8000/docs