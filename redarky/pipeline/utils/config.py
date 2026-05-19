from airflow.models import Variable

API_BASE_URL = Variable.get(
    "API_BASE_URL",
    default_var="http://localhost:8000"
)

S3_BASE_PATH = Variable.get(
    "S3_BASE_PATH",
    default_var="/mnt/d/SaaS/ListeningAIAgent/ListeningAgentAi/redarky/redarky_data_s3"
)

PG_CONN_STR = Variable.get(
    "PG_CONN_STR",
    default_var="postgresql://postgres:password@host.docker.internal:5432/redarky_db"
)

OPENAI_API_KEY = Variable.get(
    "OPENAI_API_KEY",
    default_var=""
)

DEFAULT_MISSION_ID = Variable.get(
    "DEFAULT_MISSION_ID",
    default_var="00000000-0000-0000-0000-000000000001"
)

DEFAULT_QUERY = Variable.get(
    "DEFAULT_QUERY",
    default_var="AI tools"
)