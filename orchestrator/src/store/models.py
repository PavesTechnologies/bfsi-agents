from sqlalchemy import Column, String, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class PipelineStateModel(Base):
    __tablename__ = "pipeline_states"

    application_id = Column(String, primary_key=True, index=True)
    state_json = Column(JSON, nullable=False)
