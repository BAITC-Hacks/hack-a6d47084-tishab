from .common import StrictModel


class HealthResponse(StrictModel):
    status: str
    app: str
    environment: str
    providers: dict[str, str]
