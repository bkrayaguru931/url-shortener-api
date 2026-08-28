from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class URLMapping(Base):
    """Stores the mapping between a short code and the original long URL."""

    __tablename__ = "url_mappings"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(10), unique=True, index=True, nullable=False)
    original_url = Column(String(2048), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    visit_count = Column(Integer, default=0, nullable=False)
