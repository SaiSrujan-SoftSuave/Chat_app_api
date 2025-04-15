from pydantic.v1 import BaseModel


class ChatAppResponse(BaseModel):
    """
    Base response model for all API responses.
    """

    status_code: str
    message: str | dict | None = None
    data: dict | list | str | None = None