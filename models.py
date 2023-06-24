from sqlalchemy import Column, Integer, DateTime, ForeignKey

from sqlalchemy.orm import relationship, backref

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Channel(Base):

    __tablename__ = "channel"

    channel_id = Column(Integer, primary_key=True)

    retention_hours = Column(Integer)

    last_pruned = Column(DateTime)

    guild_id = Column(Integer, ForeignKey("guild.guild_id"))


class Guild(Base):

    __tablename__ = "guild"

    guild_id = Column(Integer, primary_key=True)

    channels = relationship("Channel", backref=backref("guild"), cascade="delete")
