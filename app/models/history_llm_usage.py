import uuid
from sqlalchemy import Column, String, Float, Integer, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class HistoryLlmUsage(Base):
    """
    Mencatat setiap aktivitas penggunaan LLM:
    model yang dipakai, token usage, durasi, dan estimasi biaya.
    """
    __tablename__ = "history_llm_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Relasi ke master model LLM (nullable — tetap tercatat meski model tidak ada di master)
    mst_model_llm_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mst_model_llm.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Identitas model (disimpan langsung agar log tetap valid walau master berubah)
    model_name = Column(String(150), nullable=False, comment="Nama model LLM yang digunakan")

    # Token usage
    total_tokens = Column(Integer, nullable=True, comment="Total token (input + output)")
    input_tokens = Column(Integer, nullable=True, comment="Jumlah token input / prompt")
    output_tokens = Column(Integer, nullable=True, comment="Jumlah token output / completion")

    # Estimasi biaya (dihitung dari input_price & output_price di mst_model_llm)
    estimated_cost = Column(
        Numeric(precision=12, scale=6),
        nullable=True,
        comment="Estimasi biaya dalam USD",
    )

    # Performa
    duration_seconds = Column(Float, nullable=True, comment="Durasi pemanggilan API dalam detik")

    # Konteks tambahan
    agent_name = Column(String(100), nullable=True, comment="Nama agent yang memanggil LLM")
    run_id = Column(String(100), nullable=True, index=True, comment="ID sesi / run untuk tracing")
    module = Column(String(100), nullable=True, comment="Modul / fitur yang menggunakan LLM")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Waktu pemanggilan LLM",
    )

    # Relasi ke MstModelLlm
    mst_model_llm = relationship("MstModelLlm", back_populates="usage_histories")
