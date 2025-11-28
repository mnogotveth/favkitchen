"""initial schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


member_role_enum = sa.Enum("owner", "admin", "manager", "member", name="member_role_enum")
deal_status_enum = sa.Enum("new", "in_progress", "won", "lost", name="deal_status_enum")
deal_stage_enum = sa.Enum(
    "qualification", "proposal", "negotiation", "closed", name="deal_stage_enum"
)
activity_type_enum = sa.Enum(
    "comment", "status_changed", "stage_changed", "task_created", "system",
    name="activity_type_enum",
)


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    member_role_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "organization_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("role", member_role_enum, nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_member_org_user"),
    )

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320)),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    deal_status_enum.create(op.get_bind(), checkfirst=True)
    deal_stage_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id", ondelete="CASCADE")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("currency", sa.String(length=8), server_default="USD"),
        sa.Column("status", deal_status_enum, nullable=False, server_default="new"),
        sa.Column("stage", deal_stage_enum, nullable=False, server_default="qualification"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("deal_id", sa.Integer(), sa.ForeignKey("deals.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_done", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    activity_type_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("deal_id", sa.Integer(), sa.ForeignKey("deals.id", ondelete="CASCADE")),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("type", activity_type_enum, nullable=False),
        sa.Column("payload", sa.JSON(), default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("activities")
    activity_type_enum.drop(op.get_bind(), checkfirst=True)
    op.drop_table("tasks")
    op.drop_table("deals")
    deal_stage_enum.drop(op.get_bind(), checkfirst=True)
    deal_status_enum.drop(op.get_bind(), checkfirst=True)
    op.drop_table("contacts")
    op.drop_table("organization_members")
    member_role_enum.drop(op.get_bind(), checkfirst=True)
    op.drop_table("users")
    op.drop_table("organizations")
