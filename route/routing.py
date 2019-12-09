# -*- coding:utf-8 -*-


import asyncio
import logging
from typing import Any, Callable, Type, Union

from fastapi import params
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import solve_dependencies
from fastapi.encoders import DictIntStrAny, SetIntStr
from fastapi.exceptions import RequestValidationError
from fastapi.utils import get_field_info
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
try:
    from pydantic.fields import FieldInfo, ModelField
except ImportError:  # pragma: nocover
    # TODO: remove when removing support for Pydantic < 1.0.0
    from pydantic import Schema as FieldInfo  # type: ignore
    from pydantic.fields import Field as ModelField  # type: ignore

from fastapi.routing import APIRoute, serialize_response
from response import APIResponse


def get_request_handler(
        dependant: Dependant,
        body_field: ModelField = None,
        status_code: int = 200,
        response_class: Type[Response] = JSONResponse,
        response_field: ModelField = None,
        response_model_include: Union[SetIntStr, DictIntStrAny] = None,
        response_model_exclude: Union[SetIntStr, DictIntStrAny] = set(),
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        dependency_overrides_provider: Any = None,
) -> Callable:
    assert dependant.call is not None, "dependant.call must be a function"
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)
    is_body_form = body_field and isinstance(get_field_info(body_field), params.Form)

    async def app(request: Request) -> Response:
        try:
            body = None
            if body_field:
                if is_body_form:
                    body = await request.form()
                else:
                    body_bytes = await request.body()
                    if body_bytes:
                        body = await request.json()
        except Exception as e:
            logging.error(f"Error getting request body: {e}")
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e
        solved_result = await solve_dependencies(
            request=request,
            dependant=dependant,
            body=body,
            dependency_overrides_provider=dependency_overrides_provider,
        )
        values, errors, background_tasks, sub_response, _ = solved_result
        if errors:
            raise RequestValidationError(errors)
        else:
            assert dependant.call is not None, "dependant.call must be a function"

            if is_coroutine:
                raw_response = await dependant.call(**values)
            else:
                raw_response = await run_in_threadpool(dependant.call, **values)
            if isinstance(raw_response, Response):
                if raw_response.background is None:
                    raw_response.background = background_tasks
                return raw_response
            if isinstance(raw_response, APIResponse):
                response_data = serialize_response(
                    field=response_field,
                    response=raw_response.body,
                    include=response_model_include,
                    exclude=response_model_exclude,
                    by_alias=response_model_by_alias,
                    exclude_unset=response_model_exclude_unset,
                )
                raw_response.body = response_data
                return raw_response
            response_data = serialize_response(
                field=response_field,
                response=raw_response,
                include=response_model_include,
                exclude=response_model_exclude,
                by_alias=response_model_by_alias,
                exclude_unset=response_model_exclude_unset,
            )
            response = response_class(
                content=response_data,
                status_code=status_code,
                background=background_tasks,
            )
            response.headers.raw.extend(sub_response.headers.raw)
            if sub_response.status_code:
                response.status_code = sub_response.status_code
            return response
    return app


class NewRoute(APIRoute):
    def __init__(self, *args, **kwargs) -> None:
        super(NewRoute, self).__init__(*args, **kwargs)

    def get_route_handler(self) -> Callable:
        return get_request_handler(
            dependant=self.dependant,
            body_field=self.body_field,
            status_code=self.status_code,
            response_class=self.response_class or JSONResponse,
            response_field=self.secure_cloned_response_field,
            response_model_include=self.response_model_include,
            response_model_exclude=self.response_model_exclude,
            response_model_by_alias=self.response_model_by_alias,
            response_model_exclude_unset=self.response_model_exclude_unset,
            dependency_overrides_provider=self.dependency_overrides_provider,
        )
