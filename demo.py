from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
import uvicorn

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

resp_entities = [
    {
        "single_project_code":"1304bb19000301",
        "single_project_name":"台北500千伏变电站新建工程",
        "posid":"1304bb1900030125030501",
        "ebeln":"4500106905",
        "ebelp":"000040",
        "asset_type":"组合电器",
        "location":"台北市",
        "year":"2023"
    },
    {
        "single_project_code":"1304bb19000303",
        "single_project_name":"台北500kv输变电工程",
        "posid":"1304bb1900030125030507",
        "ebeln":"4500106907",
        "ebelp":"000049",
        "asset_type":"组合电器",
        "location":"台北市",
        "year":"2028"
    }
]
class reqmodel(BaseModel):
    single_project_code:str

class resp_model(BaseModel):
    single_project_code:str
    single_project_name:str
    posid:str
    ebeln:str
    ebelp:str
    asset_type:str
    location:str
    year:str
@app.post('/singleproject/info/detailinfo',response_model=resp_model)
async def get_single_project(req:reqmodel):
    if req.single_project_code:
        for entity in resp_entities:
            if entity['single_project_code'] == req.single_project_code:
                return entity
            else:
                return {'msg':'未查询到该实体'}
    else:
        return {
            'msg':'请先传入single_project_code'
        }

if __name__ == '__main__':
    uvicorn.run(app,host='0.0.0.0',port=8099)

