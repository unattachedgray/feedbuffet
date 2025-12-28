from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .engine import Base

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, unique=True, nullable=False)
    source_name = Column(String)
    title = Column(Text)
    description = Column(Text)
    published_at = Column(DateTime(timezone=True))
    language = Column(String)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to CourseArticle
    course_associations = relationship("CourseArticle", back_populates="article")

class Course(Base):
    __tablename__ = 'courses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_key = Column(Text, unique=True, nullable=False)
    title = Column(Text)
    summary = Column(Text)
    entities_json = Column(JSONB, default=[])
    topics_json = Column(JSONB, default=[])
    source_urls = Column(JSONB, default=[])
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article_associations = relationship("CourseArticle", back_populates="course")

class CourseArticle(Base):
    __tablename__ = 'course_articles'
    
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), primary_key=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'), primary_key=True)
    
    course = relationship("Course", back_populates="article_associations")
    article = relationship("Article", back_populates="course_associations")

class Plate(Base):
    __tablename__ = 'plates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, unique=True, nullable=False)
    visibility = Column(String, default="public") # public, unlisted, private
    rules_json = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Sauce(Base):
    __tablename__ = 'sauces'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate_id = Column(UUID(as_uuid=True), ForeignKey('plates.id'))
    name = Column(Text)
    definition_json = Column(JSONB, default={})
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    plate = relationship("Plate")

class PlateCache(Base):
    __tablename__ = 'plate_cache'
    
    plate_id = Column(UUID(as_uuid=True), ForeignKey('plates.id'), primary_key=True)
    cache_provider = Column(String, default="gemini")
    cache_name = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
