from sqlalchemy import Column, Integer, String, func, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    phone = Column(String(25))
    birthday = Column(Date)
    created_at = Column('created_at', DateTime, default=func.now(), nullable=True)
    updated_at = Column('updated_at', DateTime, default=func.now(), onupdate=func.now(), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    user = relationship('User', backref="contacts", lazy="joined")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    created_at = Column('created_at', DateTime, default=func.now())
    updated_at = Column('updated_at', DateTime, default=func.now(), onupdate=func.now())
    confirmed = Column(Boolean, default=False, nullable=True)
