"""Initial database schema migration.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Leagues
    op.create_table(
        'leagues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('short_name', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'country', name='uq_league_name_country')
    )
    op.create_index(op.f('ix_leagues_id'), 'leagues', ['id'], unique=False)

    # 2. Seasons
    op.create_table(
        'seasons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('league_id', 'year', name='uq_season_league_year')
    )
    op.create_index(op.f('ix_seasons_id'), 'seasons', ['id'], unique=False)

    # 3. Teams
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('short_name', sa.String(length=10), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=True),
        sa.Column('league_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'league_id', name='uq_team_name_league')
    )
    op.create_index(op.f('ix_teams_id'), 'teams', ['id'], unique=False)

    # 4. Matches
    op.create_table(
        'matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('home_team_id', sa.Integer(), nullable=False),
        sa.Column('away_team_id', sa.Integer(), nullable=False),
        sa.Column('match_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('result', sa.String(length=1), nullable=True),
        sa.Column('matchday', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('season_id', 'home_team_id', 'away_team_id', name='uq_match_season_teams')
    )
    op.create_index(op.f('ix_matches_id'), 'matches', ['id'], unique=False)
    op.create_index('ix_matches_match_date', 'matches', ['match_date'], unique=False)
    op.create_index('ix_matches_home_team', 'matches', ['home_team_id'], unique=False)
    op.create_index('ix_matches_away_team', 'matches', ['away_team_id'], unique=False)

    # 5. Team Match Statistics
    op.create_table(
        'team_match_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('is_home', sa.Boolean(), nullable=False),
        sa.Column('goals', sa.Integer(), nullable=True),
        sa.Column('goals_conceded', sa.Integer(), nullable=True),
        sa.Column('shots', sa.Integer(), nullable=True),
        sa.Column('shots_on_target', sa.Integer(), nullable=True),
        sa.Column('possession', sa.Float(), nullable=True),
        sa.Column('xg', sa.Float(), nullable=True),
        sa.Column('corners', sa.Integer(), nullable=True),
        sa.Column('fouls', sa.Integer(), nullable=True),
        sa.Column('yellow_cards', sa.Integer(), nullable=True),
        sa.Column('red_cards', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('match_id', 'team_id', name='uq_team_match_stat')
    )
    op.create_index(op.f('ix_team_match_statistics_id'), 'team_match_statistics', ['id'], unique=False)
    op.create_index('ix_team_match_stats_team', 'team_match_statistics', ['team_id'], unique=False)

    # 6. Standings
    op.create_table(
        'standings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('played', sa.Integer(), nullable=False),
        sa.Column('won', sa.Integer(), nullable=False),
        sa.Column('drawn', sa.Integer(), nullable=False),
        sa.Column('lost', sa.Integer(), nullable=False),
        sa.Column('goals_for', sa.Integer(), nullable=False),
        sa.Column('goals_against', sa.Integer(), nullable=False),
        sa.Column('goal_difference', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('season_id', 'team_id', name='uq_standing_season_team')
    )
    op.create_index(op.f('ix_standings_id'), 'standings', ['id'], unique=False)

    # 7. Model Versions
    op.create_table(
        'model_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version_tag', sa.String(length=50), nullable=False),
        sa.Column('algorithm', sa.String(length=50), nullable=False),
        sa.Column('training_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('log_loss', sa.Float(), nullable=True),
        sa.Column('features_json', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_tag')
    )
    op.create_index(op.f('ix_model_versions_id'), 'model_versions', ['id'], unique=False)

    # 8. Predictions
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=True),
        sa.Column('home_team_id', sa.Integer(), nullable=False),
        sa.Column('away_team_id', sa.Integer(), nullable=False),
        sa.Column('model_version_id', sa.Integer(), nullable=True),
        sa.Column('home_win_probability', sa.Float(), nullable=False),
        sa.Column('draw_probability', sa.Float(), nullable=False),
        sa.Column('away_win_probability', sa.Float(), nullable=False),
        sa.Column('predicted_result', sa.String(length=10), nullable=False),
        sa.Column('confidence', sa.String(length=10), nullable=True),
        sa.Column('explanation_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_predictions_id'), 'predictions', ['id'], unique=False)
    op.create_index('ix_predictions_created_at', 'predictions', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('predictions')
    op.drop_table('model_versions')
    op.drop_table('standings')
    op.drop_table('team_match_statistics')
    op.drop_table('matches')
    op.drop_table('teams')
    op.drop_table('seasons')
    op.drop_table('leagues')
