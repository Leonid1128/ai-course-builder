from __future__ import annotations

from django.db import transaction

from apps.courses.models import BlockRevision, ContentBlock


def record_revision(block: ContentBlock) -> BlockRevision:
    return BlockRevision.objects.create(
        block=block,
        version=block.version,
        content=block.content,
        source_meta=block.source_meta,
    )


@transaction.atomic
def reorder_blocks(items: list[dict[str, object]]) -> None:
    ids = [item["id"] for item in items]
    blocks = {str(block.id): block for block in ContentBlock.objects.filter(id__in=ids)}
    missing = [str(block_id) for block_id in ids if str(block_id) not in blocks]
    if missing:
        raise ContentBlock.DoesNotExist(f"Unknown blocks: {missing}")
    for item in items:
        block = blocks[str(item["id"])]
        block.order = int(item["order"])  # type: ignore[arg-type]
        block.save(update_fields=["order", "updated_at"])
