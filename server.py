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