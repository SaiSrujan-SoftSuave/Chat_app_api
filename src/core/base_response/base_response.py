from pydantic.v1 import BaseModel


class Response(BaseModel):
    """
    Base response model for all API responses.
    """

    status: str
    message: str | None = None
    data: any |dict | list | str | None = None

