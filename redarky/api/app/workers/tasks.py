from app.workers.celery_app import celery
import json


@celery.task
def process_batch(mission_id: str, file_path: str):
    print(f"Processing batch for mission {mission_id}")

    with open(file_path, "r") as f:
        data = json.load(f)

    # TODO:
    # validate
    # clean
    # deduplicate (redis)
    # classify
    # store in postgres

    print(f"Loaded {len(data)} items")