""""budget_exceed_resources_module"

Revision ID: b7ac802da778
Revises: f45ed78f1de9
Create Date: 2020-07-15 13:05:54.365778

"""
from datetime import datetime, timezone
import uuid

from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy.sql import table, column
from sqlalchemy import (
    Integer, insert, delete, String, TEXT, Enum, select, and_
)


# revision identifiers, used by Alembic.
revision = "b7ac802da778"
down_revision = "f45ed78f1de9"
branch_labels = None
depends_on = None

schedule_table = table(
    "schedule",
    column("id", String(length=36)),
    column("report_id", String(length=36)),
    column("recipient_id", String(length=36)),
    column("crontab", String(length=128)),
    column("last_run", Integer),
    column("next_run", Integer),
    column("created_at", Integer),
)

recipient_table = table(
    "recipient",
    column("id", String(length=36)),
    column("role_purpose", String(128)),
)

report_table = table(
    "report",
    column("id", String(length=36)),
    column("created_at", Integer()),
    column("name", String(50)),
    column("module_name", String(128)),
    column("report_format", Enum("html")),
    column("description", TEXT()),
)

CRONTAB = "0 0 * * *"
MODULE_NAME = "budget_exceed_resources"


def get_current_timestamp():
    return int(datetime.now(tz=timezone.utc).timestamp())


def gen_id():
    return str(uuid.uuid4())


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        ins_stmt = insert(report_table).values(
            id=str(uuid.uuid4()),
            created_at=get_current_timestamp(),
            name=MODULE_NAME,
            module_name=MODULE_NAME,
            report_format="html",
            description="Budget exceed resources report",
        )
        session.execute(ins_stmt)

        recipients_stmt = select([recipient_table]).where(
            recipient_table.c.role_purpose == "optscale_engineer"
        )
        budget_exceed_resources_stmt = select([report_table]).where(
            report_table.c.module_name == MODULE_NAME
        )
        schedules = []
        now = get_current_timestamp()
        for budget_exceed_resources_report in session.execute(
            budget_exceed_resources_stmt
        ):
            for engineer in session.execute(recipients_stmt):
                schedules.append(
                    {
                        "id": gen_id(),
                        "report_id": budget_exceed_resources_report["id"],
                        "recipient_id": engineer["id"],
                        "crontab": CRONTAB,
                        "last_run": 0,
                        "next_run": now,
                        "created_at": now,
                    }
                )
            op.bulk_insert(schedule_table, schedules)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        recipients_stmt = select([recipient_table]).where(
            recipient_table.c.role_purpose == "optscale_engineer"
        )
        engineers = session.execute(recipients_stmt)
        engineers_ids = list(map(lambda x: x["id"], engineers))
        budget_exceed_res_stmt = select([report_table]).where(
            report_table.c.module_name == MODULE_NAME
        )
        for budget_exceed_res_report in session.execute(
                budget_exceed_res_stmt):
            delete_schedule_stmt = delete(schedule_table).where(
                and_(
                    schedule_table.c.report_id == budget_exceed_res_report[
                        "id"],
                    schedule_table.c.recipient_id.in_(engineers_ids),
                )
            )
            session.execute(delete_schedule_stmt)
        ins_stmt = delete(report_table).where(
            report_table.c.module_name == MODULE_NAME)
        session.execute(ins_stmt)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    # ### end Alembic commands ###
