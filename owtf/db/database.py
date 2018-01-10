"""
owtf.db.db
~~~~~~~~~~

This file handles all the database transactions.
"""
import functools
import logging

from sqlalchemy import create_engine, exc, func
from sqlalchemy.orm import Session as _Session, sessionmaker

from owtf.db.models import Base
from owtf.settings import DATABASE_IP, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PASS


def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


def flush_transaction(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        dryrun = kwargs.pop("dryrun", False)
        try:
            ret = method(self, *args, **kwargs)
            if dryrun:
                self.session.rollback()
            else:
                self.session.flush()
        except Exception:
            logging.exception("Transaction Failed. Rolling back.")
            if self.session is not None:
                self.session.rollback()
            raise
        return ret
    return wrapper


def get_db_engine():
    engine = create_engine(
            "postgresql+psycopg2://{}:{}@{}:{}/{}".format(DATABASE_USER, DATABASE_PASS, DATABASE_IP, int(DATABASE_PORT),
            DATABASE_NAME), pool_recycle=120)
    Base.metadata.create_all(engine)
    return engine


def get_scoped_session():
    Session.configure(bind=get_db_engine())
    return Session()


class Session(_Session):
    """ Custom session meant to utilize add on the model.
        This Session overrides the add/add_all methods to prevent them
        from being used. This is to for using the add methods on the
        models themselves where overriding is available.
    """

    _add = _Session.add
    _add_all = _Session.add_all
    _delete = _Session.delete

Session = sessionmaker(class_=Session)
