from app.ai.models import Agent, AgentRun
from app.auth.models import User, RedditCredential
from app.data.models import Report, EngagementAction, DataItem, Embedding, MarketGap, PipelineBatch
from app.missions.models import Mission
from app.keywords.models import Keyword
from app.projects.models import Project
from app.posts.models import Post
from app.leads.models import Lead

from app.database import Base

# Export them for easy access elsewhere
__all__ = [
    "Base",
    "User",
    "RedditCredential",
    "Mission",
    "Report",
    "EngagementAction",
    "DataItem",
    "Embedding",
    "MarketGap",
    "Agent",
]
# __all__ = [
#     "Base",
#     "User",
#     "RedditCredential",
#     "Mission",
#     "Report",
#     "EngagementAction",
#     "DataItem",
#     "Embedding",
#     "MarketGap",
#     "Agent",
#     "AgentRun",
#     "PipelineBatch",
# ]