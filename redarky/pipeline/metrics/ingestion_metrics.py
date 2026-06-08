from pipeline.utils.logger import log


def record_ingestion_metrics(
    batch_id: str,
    mission_id: str,
    inserted: int,
    skipped: int,
    duration_seconds: float,
) -> None:

    throughput = 0

    total = inserted + skipped

    if duration_seconds > 0:
        throughput = round(total / duration_seconds, 2)

    log.info(
        "pipeline.metrics",
        batch_id=batch_id,
        mission_id=mission_id,
        inserted=inserted,
        skipped=skipped,
        throughput_per_second=throughput,
        duration_seconds=duration_seconds,
    )