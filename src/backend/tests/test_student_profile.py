"""
Tests for student profile tools (SQLite CRUD).
"""

import pytest
import os
import tempfile

from app.models.database import init_db, get_db
from app.models.schemas import StudentProfile
from app.tools.student_profile import (
    get_student_profile,
    save_student_profile,
    update_student_profile,
    has_complete_info,
    get_missing_info_message,
)


class TestStudentProfile:
    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Set up a temporary database for testing."""
        import app.config as cfg
        self._old_path = cfg.settings.sqlite_path
        self._tmp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cfg.settings.sqlite_path = self._tmp_db.name
        init_db()
        yield
        cfg.settings.sqlite_path = self._old_path
        os.unlink(self._tmp_db.name)

    def test_get_nonexistent_profile(self):
        profile = get_student_profile("no_such_student")
        assert profile is None

    def test_save_and_get_profile(self):
        profile = StudentProfile(
            student_id="s1",
            name="小明",
            age=15,
            education="初中三年级",
            is_weak_foundation=True,
        )
        save_student_profile(profile)

        retrieved = get_student_profile("s1")
        assert retrieved is not None
        assert retrieved.name == "小明"
        assert retrieved.age == 15
        assert retrieved.education == "初中三年级"
        assert retrieved.is_weak_foundation is True

    def test_update_profile(self):
        # First save
        profile = StudentProfile(
            student_id="s2",
            name="小红",
            age=12,
            education="小学六年级",
        )
        save_student_profile(profile)

        # Update
        updated = update_student_profile("s2", age=13, education="初中一年级")
        assert updated.age == 13
        assert updated.education == "初中一年级"

    def test_has_complete_info(self):
        # Incomplete profile
        assert has_complete_info("s3") is False

        profile = StudentProfile(
            student_id="s3",
            name="张三",
            age=20,
            education="大学三年级",
        )
        save_student_profile(profile)
        assert has_complete_info("s3") is True

    def test_get_missing_info_message_new_student(self):
        msg = get_missing_info_message("new_student")
        assert msg is not None
        assert "名字" in msg or "name" in msg.lower() or "你好" in msg

    def test_get_missing_info_message_complete(self):
        profile = StudentProfile(
            student_id="s4",
            name="李四",
            age=18,
            education="高中三年级",
        )
        save_student_profile(profile)
        msg = get_missing_info_message("s4")
        assert msg is None  # complete profile → no missing

    def test_is_complete_method(self):
        incomplete = StudentProfile(student_id="id1", name="name")
        assert incomplete.is_complete() is False

        complete = StudentProfile(
            student_id="id2",
            name="name",
            age=20,
            education="大学",
        )
        assert complete.is_complete() is True

    def test_missing_fields(self):
        profile = StudentProfile(student_id="id1", name="name")
        missing = profile.missing_fields()
        assert "age" in missing
        assert "education" in missing
        assert "name" not in missing