import asyncio
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.ai.service import gap_finder_agent, researcher_agent, supervisor_agent
from app.data.schemas import RawItemSchema
from app.data.service import generate_hash, transform_to_model
from app.database import SessionLocal
from app.models import Agent, AgentRun, DataItem, MarketGap, Report
from app.storage.local_s3 import LocalS3Storage
from app.utils.redis_client import is_duplicate
from app.workers.celery_app import celery
from app.config import settings

storage = LocalS3Storage()


async def _get_or_create_agent(session, name: str, role: str) -> Agent:
    result = await session.execute(select(Agent).where(Agent.name == name))
    agent = result.scalar_one_or_none()
    if agent:
        return agent
    agent = Agent(name=name, role=role, config={"version": "phase3-core"})
    session.add(agent)
    await session.flush()
    return agent


async def _record_agent_run(session, mission_id: str, agent_id, status: str, output_payload: dict) -> None:
    run = AgentRun(
        mission_id=mission_id,
        agent_id=agent_id,
        status=status,
        input_payload={},
        output_payload=output_payload,
        ended_at=datetime.now(UTC),
    )
    session.add(run)


# @celery.task(name="app.workers.tasks.process_batch")
# def process_batch(mission_id: str, file_path: str):
#     asyncio.run(_process_batch_async(mission_id, file_path))

import asyncio

@celery.task
def process_batch(mission_id, file_path):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We are in Eager mode (FastAPI's loop is active)
        # We must return a future/coroutine or use ensure_future
        return asyncio.ensure_future(_process_batch_async(mission_id, file_path))
    else:
        # We are in a normal Celery worker process (no loop exists)
        return asyncio.run(_process_batch_async(mission_id, file_path))

async def _process_batch_async(mission_id: str, file_path: str) -> None:
    print(f"Processing batch: {file_path}")
    raw_data = storage.read_json(file_path)
    processed_payload: list[dict] = []
    dead_letter_payload: list[dict] = []
    inserted_ids: list[str] = []
    skipped = 0

    async with SessionLocal() as db:
        for item in raw_data:
            try:
                print("RAW DATA ITEM: ", item)
                validated = RawItemSchema.model_validate(item)
                print("VALIDATED RAW ITEM: ", validated)
                hash_key = generate_hash(validated)
                if is_duplicate(mission_id, hash_key):
                    skipped += 1
                    print("DUPLICATE REDIS")
                    continue

                db_item = transform_to_model(validated, mission_id, hash_key)
                print("TRANSFORMED TO MODEL: ", db_item)
                stmt = (
                    insert(DataItem)
                    .values(
                        id=db_item.id,
                        mission_id=db_item.mission_id,
                        source=db_item.source,
                        external_id=db_item.external_id,
                        dedup_hash=db_item.dedup_hash,
                        title=db_item.title,
                        content=db_item.content,
                        url=db_item.url,
                        author=db_item.author,
                        score=db_item.score,
                        classification=db_item.classification,
                        sentiment_score=db_item.sentiment_score,
                        scraped_at=db_item.scraped_at,
                        created_at=db_item.created_at,
                    )
                    .on_conflict_do_nothing(index_elements=["mission_id", "dedup_hash"])
                    .returning(DataItem.id)
                )
                result = await db.execute(stmt)
                inserted_id = result.scalar_one_or_none()
                print("INSERTED: ", inserted_id)
                if inserted_id:
                    inserted_ids.append(str(inserted_id))
                    processed_payload.append(validated.model_dump(mode="json"))
                else:
                    skipped += 1
                    print("SKIPPED LAST")
            except Exception as exc:
                dead_letter_payload.append({"item": item, "error": str(exc)})
                print("EXCEPTION: ", exc)

        await db.commit()

        if inserted_ids:
            inserted_items = (
                await db.execute(select(DataItem).where(DataItem.id.in_(inserted_ids)))
            ).scalars().all()

            researcher = await _get_or_create_agent(db, "researcher", "research")
            gaps_agent = await _get_or_create_agent(db, "gap_finder", "gap_detection")
            supervisor = await _get_or_create_agent(db, "supervisor", "orchestration")

            research_output = researcher_agent(list(inserted_items))
            gaps_output = gap_finder_agent(list(inserted_items))
            supervisor_output = supervisor_agent(research_output, gaps_output)

            await _record_agent_run(db, mission_id, researcher.id, "completed", research_output)
            await _record_agent_run(db, mission_id, gaps_agent.id, "completed", {"gaps": gaps_output})
            await _record_agent_run(db, mission_id, supervisor.id, "completed", supervisor_output)

            for gap in gaps_output:
                db.add(
                    MarketGap(
                        mission_id=mission_id,
                        title=gap["title"],
                        description=gap["description"],
                        confidence=gap["confidence"],
                        evidence=gap["evidence"],
                    )
                )

            db.add(
                Report(
                    mission_id=mission_id,
                    report_type="mission_summary",
                    content={
                        "supervisor": supervisor_output,
                        "researcher": research_output,
                        "gaps": gaps_output,
                    },
                )
            )

            # TODO: AIRFLOW_INTEGRATION - This logic will eventually be triggered/monitored by the mission_intelligence_dag.
            await db.commit()

    if processed_payload:
        storage.write_json("processed", mission_id, processed_payload)
        print("PROCESSED: ")
    if dead_letter_payload:
        storage.write_json("dead-letter", mission_id, dead_letter_payload)
        print("DEAD LETTER: ")

    print(f"Inserted: {len(inserted_ids)}, Skipped: {skipped}, Redis: {settings.REDIS_URL}")