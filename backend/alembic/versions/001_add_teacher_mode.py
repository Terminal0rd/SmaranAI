"""Add Teacher Mode tables

Revision ID: 001_add_teacher_mode
Revises: 
Create Date: 2026-01-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '001_add_teacher_mode'
down_revision = None  # Update this if there are existing migrations
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create teacher_roadmaps table
    op.create_table(
        'teacher_roadmaps',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('goal', sa.String(500), nullable=True),
        sa.Column('total_modules', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_modules', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overall_progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_teacher_roadmaps_user_id'), 'teacher_roadmaps', ['user_id'])
    
    # Create teacher_modules table
    op.create_table(
        'teacher_modules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('roadmap_id', sa.String(), nullable=False),
        sa.Column('module_index', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('level', sa.Enum('beginner', 'intermediate', 'advanced', name='modulelevel'), nullable=False),
        sa.Column('objectives', JSON(), nullable=False),
        sa.Column('topics', JSON(), nullable=False),
        sa.Column('prerequisites', JSON(), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('status', sa.Enum('locked', 'in_progress', 'mastered', name='modulestatus'), nullable=False, server_default='locked'),
        sa.Column('mastery_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['roadmap_id'], ['teacher_roadmaps.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_teacher_modules_roadmap_id'), 'teacher_modules', ['roadmap_id'])
    
    # Create teacher_lesson_states table
    op.create_table(
        'teacher_lesson_states',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('module_id', sa.String(), nullable=False),
        sa.Column('current_phase', sa.Enum('teach', 'check', 'reteach', name='lessonphase'), nullable=False, server_default='teach'),
        sa.Column('check_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('teach_content', sa.Text(), nullable=True),
        sa.Column('reteach_content', sa.Text(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['module_id'], ['teacher_modules.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('module_id'),
    )
    op.create_index(op.f('ix_teacher_lesson_states_module_id'), 'teacher_lesson_states', ['module_id'])
    
    # Create teacher_check_attempts table
    op.create_table(
        'teacher_check_attempts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('module_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('questions', JSON(), nullable=False),
        sa.Column('answers', JSON(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('passed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('weak_topics', JSON(), nullable=True),
        sa.Column('grading_details', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['module_id'], ['teacher_modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_teacher_check_attempts_module_id'), 'teacher_check_attempts', ['module_id'])
    op.create_index(op.f('ix_teacher_check_attempts_user_id'), 'teacher_check_attempts', ['user_id'])
    
    # Create teacher_memory_cards table
    op.create_table(
        'teacher_memory_cards',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('module_id', sa.String(), nullable=False),
        sa.Column('card_type', sa.Enum('concept', 'formula', 'mistake', 'example', name='cardtype'), nullable=False),
        sa.Column('front_text', sa.Text(), nullable=False),
        sa.Column('back_text', sa.Text(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['module_id'], ['teacher_modules.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_teacher_memory_cards_module_id'), 'teacher_memory_cards', ['module_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_teacher_memory_cards_module_id'), table_name='teacher_memory_cards')
    op.drop_table('teacher_memory_cards')
    
    op.drop_index(op.f('ix_teacher_check_attempts_user_id'), table_name='teacher_check_attempts')
    op.drop_index(op.f('ix_teacher_check_attempts_module_id'), table_name='teacher_check_attempts')
    op.drop_table('teacher_check_attempts')
    
    op.drop_index(op.f('ix_teacher_lesson_states_module_id'), table_name='teacher_lesson_states')
    op.drop_table('teacher_lesson_states')
    
    op.drop_index(op.f('ix_teacher_modules_roadmap_id'), table_name='teacher_modules')
    op.drop_table('teacher_modules')
    
    op.drop_index(op.f('ix_teacher_roadmaps_user_id'), table_name='teacher_roadmaps')
    op.drop_table('teacher_roadmaps')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS modulelevel')
    op.execute('DROP TYPE IF EXISTS modulestatus')
    op.execute('DROP TYPE IF EXISTS lessonphase')
    op.execute('DROP TYPE IF EXISTS cardtype')
