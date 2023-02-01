#  Copyright (c) ZenML GmbH 2023. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""SQLModel implementation of build output tables."""


from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import TEXT, Column
from sqlmodel import Field, Relationship

from zenml.config.build_configuration import BuildOutput
from zenml.models import BuildOutputRequestModel, BuildOutputResponseModel
from zenml.zen_stores.schemas.base_schemas import BaseSchema
from zenml.zen_stores.schemas.pipeline_schemas import PipelineSchema
from zenml.zen_stores.schemas.schema_utils import build_foreign_key_field
from zenml.zen_stores.schemas.stack_schemas import StackSchema
from zenml.zen_stores.schemas.user_schemas import UserSchema
from zenml.zen_stores.schemas.workspace_schemas import WorkspaceSchema

if TYPE_CHECKING:
    from zenml.zen_stores.schemas.pipeline_run_schemas import PipelineRunSchema


class BuildOutputSchema(BaseSchema, table=True):
    """SQL Model for pipeline build outputs."""

    __tablename__ = "build_output"

    user_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=UserSchema.__tablename__,
        source_column="user_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    user: Optional["UserSchema"] = Relationship(back_populates="builds")

    workspace_id: UUID = build_foreign_key_field(
        source=__tablename__,
        target=WorkspaceSchema.__tablename__,
        source_column="workspace_id",
        target_column="id",
        ondelete="CASCADE",
        nullable=False,
    )
    workspace: "WorkspaceSchema" = Relationship(back_populates="builds")

    stack_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=StackSchema.__tablename__,
        source_column="stack_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    stack: Optional["StackSchema"] = Relationship(back_populates="builds")

    pipeline_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=PipelineSchema.__tablename__,
        source_column="pipeline_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    pipeline: Optional["PipelineSchema"] = Relationship(
        back_populates="builds"
    )

    runs: List["PipelineRunSchema"] = Relationship(back_populates="build")

    configuration: str = Field(sa_column=Column(TEXT, nullable=False))

    @classmethod
    def from_request(
        cls, request: BuildOutputRequestModel
    ) -> "BuildOutputSchema":
        """Convert a `BuildOutputRequestModel` to a `BuildOutputSchema`.

        Args:
            request: The request to convert.

        Returns:
            The created `BuildOutputSchema`.
        """
        configuration = request.configuration.json()

        return cls(
            id=request.id,
            stack_id=request.stack,
            workspace_id=request.workspace,
            user_id=request.user,
            pipeline_id=request.pipeline,
            configuration=configuration,
        )

    def to_model(
        self,
    ) -> BuildOutputResponseModel:
        """Convert a `BuildOutputSchema` to a `BuildOutputResponseModel`.

        Returns:
            The created `BuildOutputResponseModel`.
        """
        return BuildOutputResponseModel(
            id=self.id,
            configuration=BuildOutput.parse_raw(self.configuration),
            workspace=self.workspace.to_model(),
            user=self.user.to_model(True) if self.user else None,
            stack=self.stack.to_model() if self.stack else None,
            pipeline=(
                self.pipeline.to_model(False) if self.pipeline else None
            ),
            created=self.created,
            updated=self.updated,
        )
