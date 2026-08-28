from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict


class URLShortenRequest(BaseModel):
    """Request body for POST /shorten."""
    url: HttpUrl


class URLShortenResponse(BaseModel):
    """Response body returned after a URL has been shortened."""
    short_code: str
    short_url: str
    original_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class URLStatsResponse(BaseModel):
    """Optional response body for inspecting a short code's stats."""
    short_code: str
    original_url: str
    visit_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
