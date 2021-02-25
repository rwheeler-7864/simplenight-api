import json
from typing import List, Union, TypeVar, Type

from pydantic.main import BaseModel


class SimplenightModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class BusinessContact(SimplenightModel):
    name: str
    email: str
    website: str
    address: str
    phones: List[str]


class BusinessLocation(SimplenightModel):
    latitude: float
    longitude: float
    address: str


T = TypeVar("T")


def from_json(obj, cls: Type[T], many=False) -> Union[List[T], T]:
    if many:
        return list(map(cls.parse_obj, json.loads(obj)))

    if isinstance(obj, (str, bytes)):
        return cls.parse_raw(obj)

    return cls.parse_obj(obj)


def to_json(obj: Union[SimplenightModel, List[SimplenightModel]], many=False, indent=2):
    class ItemList(SimplenightModel):
        __root__: List[SimplenightModel]

    if many:
        return ItemList.parse_obj(obj).json(indent=indent)

    return obj.json(indent=indent)
