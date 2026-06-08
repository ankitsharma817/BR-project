from typing import Generic, TypeVar, Any
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class MessageResponse(BaseModel):
    message: str
