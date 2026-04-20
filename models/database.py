from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional, List
import json
import os

from config import ItemCategory, SecondaryTag, GenerateMode, APIProvider, settings

Base = declarative_base()


class GenerationRecord(Base):
    __tablename__ = "generation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False, index=True)
    
    category = Column(String(32), nullable=False)
    secondary_tags = Column(Text, default="[]")
    mode = Column(String(16), nullable=False)
    
    input_type = Column(String(16), nullable=False)
    input_data = Column(Text, nullable=False)
    input_file_path = Column(String(512), nullable=True)
    
    provider = Column(String(32), nullable=False)
    job_id = Column(String(128), nullable=True, index=True)
    model_url = Column(Text, nullable=True)
    preview_url = Column(Text, nullable=True)
    model_file_path = Column(String(512), nullable=True)
    
    status = Column(String(16), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def get_secondary_tags(self) -> List[str]:
        return json.loads(self.secondary_tags) if self.secondary_tags else []
    
    def set_secondary_tags(self, tags: List[str]):
        self.secondary_tags = json.dumps(tags)


class UserAPIKey(Base):
    __tablename__ = "user_api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(32), unique=True, nullable=False)
    api_key = Column(Text, nullable=False)
    secret_key = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Database:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or settings.database_url
        self.engine = create_engine(self.db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables()
    
    def _create_tables(self):
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        return self.Session()
    
    def create_record(
        self,
        task_id: str,
        category: str,
        secondary_tags: List[str],
        mode: str,
        input_type: str,
        input_data: str,
        provider: str,
        input_file_path: str = None,
    ) -> GenerationRecord:
        session = self.get_session()
        try:
            record = GenerationRecord(
                task_id=task_id,
                category=category,
                secondary_tags=json.dumps(secondary_tags),
                mode=mode,
                input_type=input_type,
                input_data=input_data,
                input_file_path=input_file_path,
                provider=provider,
                status="pending",
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()
    
    def update_record(
        self,
        task_id: str,
        status: str = None,
        job_id: str = None,
        model_url: str = None,
        preview_url: str = None,
        model_file_path: str = None,
        input_file_path: str = None,
        error_message: str = None,
    ) -> Optional[GenerationRecord]:
        session = self.get_session()
        try:
            record = session.query(GenerationRecord).filter_by(task_id=task_id).first()
            if record:
                if status:
                    record.status = status
                if job_id:
                    record.job_id = job_id
                if model_url:
                    record.model_url = model_url
                if preview_url:
                    record.preview_url = preview_url
                if model_file_path:
                    record.model_file_path = model_file_path
                if input_file_path is not None:
                    record.input_file_path = input_file_path
                if error_message:
                    record.error_message = error_message
                if status in ["completed", "failed"]:
                    record.completed_at = datetime.utcnow()
                session.commit()
                session.refresh(record)
            return record
        finally:
            session.close()
    
    def get_record(self, task_id: str) -> Optional[GenerationRecord]:
        session = self.get_session()
        try:
            return session.query(GenerationRecord).filter_by(task_id=task_id).first()
        finally:
            session.close()
    
    def get_records(
        self,
        category: str = None,
        provider: str = None,
        status: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[GenerationRecord]:
        session = self.get_session()
        try:
            query = session.query(GenerationRecord)
            if category:
                query = query.filter_by(category=category)
            if provider:
                query = query.filter_by(provider=provider)
            if status:
                query = query.filter_by(status=status)
            return query.order_by(GenerationRecord.created_at.desc()).offset(offset).limit(limit).all()
        finally:
            session.close()
    
    def delete_record(self, task_id: str) -> bool:
        session = self.get_session()
        try:
            record = session.query(GenerationRecord).filter_by(task_id=task_id).first()
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def save_api_key(self, provider: str, api_key: str, secret_key: str = None):
        session = self.get_session()
        try:
            existing = session.query(UserAPIKey).filter_by(provider=provider).first()
            if existing:
                existing.api_key = api_key
                existing.secret_key = secret_key
                existing.updated_at = datetime.utcnow()
            else:
                new_key = UserAPIKey(
                    provider=provider,
                    api_key=api_key,
                    secret_key=secret_key,
                )
                session.add(new_key)
            session.commit()
        finally:
            session.close()
    
    def get_api_key(self, provider: str) -> Optional[dict]:
        session = self.get_session()
        try:
            record = session.query(UserAPIKey).filter_by(provider=provider).first()
            if record:
                return {
                    "api_key": record.api_key,
                    "secret_key": record.secret_key,
                }
            return None
        finally:
            session.close()
    
    def get_all_api_keys(self) -> dict:
        session = self.get_session()
        try:
            records = session.query(UserAPIKey).all()
            return {r.provider: {"api_key": r.api_key, "secret_key": r.secret_key} for r in records}
        finally:
            session.close()


db = Database()
