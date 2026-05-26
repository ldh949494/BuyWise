"""Admin API schemas."""

from app.schemas.common import BaseSchema
from app.schemas.product import ProductRead


class AdminLoginRequest(BaseSchema):
    username: str
    password: str


class AdminTokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminProductWriteResponse(BaseSchema):
    product: ProductRead
    index_sync_status: str = "attempted"
    index_sync_note: str = "Product index sync is best-effort; check logs if search results do not update."
