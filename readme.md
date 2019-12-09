# fastapi-route
fastapi-route 是用于 fastapi 的 route。与fastapi自带的APIRoute相比，
他既能设置响应的请求头，又能对响应体进行模型检查。
### 使用示例
main.py
```python

from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from route.response import APIResponse
from route.routing import NewRoute


fake_items_db = [
    {"item_name": "Foo", "age": 18},
    {"item_name": "Bar", "age": 29},
    {"item_name": "Baz", "age": {"xxx": "yyy"}}
]

router = APIRouter(route_class=NewRoute)

class ItemModel(BaseModel):
    item_name: str
    age: int


@router.get(
    "/items/",
    response_model=ItemModel
)
async def read_item(index: int):
    item = fake_items_db[index]
    response = APIResponse(
        headers={"name": item.get("item_name"), "age": str(item.get("age"))},
        content=item
    )
    response.headers["AAA"] = "AAA"
    return response


app = FastAPI()
app.include_router(router)
```
运行：
```
uvicorn main:app
```
- 请求一
```
curl http://127.0.0.1:8000/items/?index=0
```
返回
```
StatusCode        : 200
StatusDescription : OK
Content           : {"item_name":"Foo","age":18}
RawContent        : HTTP/1.1 200 OK
                    name: Foo
                    age: 18
                    aaa: AAA
                    Content-Length: 28
                    Content-Type: application/json
                    Date: Mon, 09 Dec 2019 02:40:25 GMT
                    Server: uvicorn

                    {"item_name":"Foo","age":18}
Forms             : {}
Headers           : {[name, Foo], [age, 18], [aaa, AAA], [Content-Length, 28]...}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : System.__ComObject
RawContentLength  : 28
```
- 请求二
```
curl http://127.0.0.1:8000/items/?index=2
```
返回
```
Internal Server Error
```
查看服务端异常：
```
pydantic.error_wrappers.ValidationError: 1 validation error for ItemModel
response -> age
  value is not a valid integer (type=type_error.integer)
```
由于index=2的数据的age字段不满足类型要求，会触发异常。