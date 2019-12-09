# fastapi-route
fastapi-route 是用于 fastapi 的 route。与fastapi自带的APIRoute相比，
他既能设置响应的请求头，又能对响应体进行模型检查。
### 使用示例
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
