from pydantic import BaseModel

class MissionCreate(BaseModel):
    name: str
    goal: str

class MissionOut(BaseModel):
    id: str
    name: str
    goal: str