"""Test the resume schema without loading credentials or the application database."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.schema import CreateTable


class ResumeModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        extensions = ModuleType("extensions.extensions")
        extensions.Base = declarative_base()
        path = Path(__file__).resolve().parents[1] / "models" / "resumes.py"
        spec = importlib.util.spec_from_file_location("resume_model_under_test", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"extensions.extensions": extensions}):
            spec.loader.exec_module(module)
        cls.Resume = module.Resume
        cls.base = extensions.Base

    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        self.addCleanup(self.engine.dispose)
        self.base.metadata.create_all(self.engine)

    def values(self, **overrides):
        values = dict(user_id=uuid4(), original_filename="resume.pdf",
                      storage_key=f"resumes/{uuid4()}.pdf", file_type="pdf",
                      size_bytes=1024, file_sha256="a" * 64)
        values.update(overrides)
        return values

    def test_defaults_and_uuid_round_trip(self):
        with Session(self.engine) as session:
            resume = self.Resume(**self.values())
            session.add(resume)
            session.commit()
            self.assertIsInstance(resume.resume_id, UUID)
            self.assertEqual(resume.validation_status, "pending")
            self.assertIsNotNone(resume.created_at)
            self.assertIsNone(resume.validation_error)

    def test_invalid_metadata_is_rejected(self):
        for values in ({"size_bytes": 0}, {"size_bytes": -1}, {"file_type": "txt"},
                       {"validation_status": "unknown"}, {"file_sha256": "short"},
                       {"original_filename": " "}, {"storage_key": " "}, {"user_id": None}):
            with self.subTest(values=values), Session(self.engine) as session:
                session.add(self.Resume(**self.values(**values)))
                with self.assertRaises(IntegrityError):
                    session.commit()

    def test_storage_key_is_unique(self):
        with Session(self.engine) as session:
            session.add(self.Resume(**self.values(storage_key="resumes/same.pdf")))
            session.commit()
            session.add(self.Resume(**self.values(storage_key="resumes/same.pdf")))
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_identical_files_can_belong_to_different_uploads(self):
        with Session(self.engine) as session:
            first, second = self.Resume(**self.values()), self.Resume(**self.values())
            session.add_all([first, second])
            session.commit()
            self.assertNotEqual(first.resume_id, second.resume_id)

    def test_postgresql_schema_and_separation(self):
        table = self.Resume.__table__
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        self.assertIn("resume_id UUID NOT NULL", ddl)
        self.assertIn("TIMESTAMP WITH TIME ZONE", ddl)
        self.assertTrue(table.c.user_id.index)
        for column in ("job_description", "parsed_resume", "format_score"):
            self.assertNotIn(column, table.c)


if __name__ == "__main__":
    unittest.main()
