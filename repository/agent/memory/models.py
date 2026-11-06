from pydantic import BaseModel, Field

class Memory(BaseModel):
    key: str = Field(description="Unique key identifying the memory")
    content: str = Field(description="The actual knowledge or information stored")
    metadata: dict = Field(default_factory=dict, description="Optional metadata (e.g. source)")