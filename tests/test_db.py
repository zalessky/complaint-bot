import pytest
import aiosqlite
import os
from datetime import datetime

from utils.dto import ComplaintDTO
from utils.db import init_db, add_complaint, get_stats, ComplaintStatus, update_complaint_status, get_last_complaints

# Use an in-memory database for testing
TEST_DB = ":memory:"

@pytest.fixture(autouse=True)
async def setup_database():
    """Fixture to set up and tear down the database for each test."""
    os.environ['DB_FILE'] = TEST_DB # Override for tests
    # This is a simplified way. Ideally, db path should be passed explicitly.
    # For this project, we can mock the DB_FILE_PATH constant in db.py if needed.
    # But for aiosqlite, :memory: is fine.
    await init_db()
    yield
    # No teardown needed for in-memory db

@pytest.mark.asyncio
async def test_add_and_get_complaint():
    """Tests adding a new complaint and retrieving it."""
    dto = ComplaintDTO(
        user_id=123,
        complaint_type_id=1,
        complaint_type_name="Курение",
        route_number="28",
        direction="в центр",
        violation_datetime=datetime.now(),
        media_file_ids=["file1", "file2"]
    )
    complaint_id = await add_complaint(dto)
    assert complaint_id == 1

    last_complaints = await get_last_complaints(1)
    assert len(last_complaints) == 1
    assert last_complaints[0]['id'] == 1
    assert last_complaints[0]['route_number'] == "28"

    # Check media files were added
    async with aiosqlite.connect(TEST_DB) as db:
        async with db.execute("SELECT file_id FROM media WHERE complaint_id = ?", (complaint_id,)) as cursor:
            media_rows = await cursor.fetchall()
            assert len(media_rows) == 2
            assert {row[0] for row in media_rows} == {"file1", "file2"}

@pytest.mark.asyncio
async def test_stats_and_status_update():
    """Tests statistics calculation and status updates."""
    # Add a couple of complaints
    await add_complaint(ComplaintDTO(user_id=1, complaint_type_id=1, complaint_type_name="Курение", route_number="A"))
    await add_complaint(ComplaintDTO(user_id=2, complaint_type_id=2, complaint_type_name="Скорость", route_number="B"))
    await add_complaint(ComplaintDTO(user_id=1, complaint_type_id=1, complaint_type_name="Курение", route_number="C"))

    stats = await get_stats()
    assert stats['total_all_time'] == 3
    assert stats['total_today'] == 3
    assert len(stats['by_type']) == 2
    assert stats['by_type'][0]['complaint_type_name'] == "Курение"
    assert stats['by_type'][0]['count'] == 2

    # Test status update
    updated = await update_complaint_status(2, ComplaintStatus.IN_WORK)
    assert updated is True
    async with aiosqlite.connect(TEST_DB) as db:
        async with db.execute("SELECT status FROM complaints WHERE id = ?", (2,)) as cursor:
            row = await cursor.fetchone()
            assert row[0] == "in_work"
    
    not_updated = await update_complaint_status(999, ComplaintStatus.OK)
    assert not_updated is False
