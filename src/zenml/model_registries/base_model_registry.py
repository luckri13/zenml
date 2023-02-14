#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
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
"""Base class for all ZenML model registries."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Type, cast

from pydantic import BaseModel, Field, root_validator

from zenml.enums import StackComponentType
from zenml.stack import Flavor, StackComponent
from zenml.stack.stack_component import StackComponentConfig


class ModelVersionStage(Enum):
    """Enum of the possible stages of a registered model."""

    NONE = "None"
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"


class ModelRegistration(BaseModel):
    """Base class for all ZenML registered models.

    Model Registration are the top-level entities in the model registry.
    They serve as a container for all the versions of a model.

    Attributes:
        name: Name of the registered model.
        description: Description of the registered model.
        tags: Tags associated with the registered model.
    """

    name: str
    description: Optional[str]
    tags: Optional[Dict[str, str]] = None


class ZenMLModelMetadata(BaseModel):
    """Base class for all ZenML model metadata.

    The `ZenMLModelMetadata` class represents the metadata associated with a
    model version. It includes information about the ZenML version, pipeline run
    ID, pipeline run name, and pipeline step.

    Attributes:
        zenml_version: The ZenML version used to create this model version.
        zenml_pipeline_run_id: The pipeline run ID used to create this model version.
        zenml_pipeline_name: The pipeline name used to create this model version.
        zenml_step_name: The pipeline step name used to create this model version.
    """

    zenml_version: Optional[str] = None
    zenml_pipeline_run_id: Optional[str] = None
    zenml_pipeline_name: Optional[str] = None
    zenml_step_name: Optional[str] = None


class ModelVersion(BaseModel):
    """Base class for all ZenML model versions.

    The `ModelVersion` class represents a version or snapshot of a registered
    model, including information such as the associated `ModelBundle`, version
    number, creation time, pipeline run information, and metadata. It serves as
    a blueprint for creating concrete model version implementations in a registry,
    and provides a record of the history of a model and its development process.

    All model registries must extend this class with their own specific fields.

    Attributes:
        model_registration: The registered model associated with this model
        model_source_uri: The URI of the model bundle associated with this model
        version: The version number of this model version
        version_description: The description of this model version
        created_at: The creation time of this model version
        last_updated_at: The last updated time of this model version
        version_stage: The current stage of this model version
        version_tags: Tags associated with this model version
        registry_metadata: The metadata associated with this model version
    """

    model_registration: ModelRegistration
    model_source_uri: str
    version_description: Optional[str] = None
    version: Optional[str] = None
    created_at: Optional[int] = None
    last_updated_at: Optional[int] = None
    version_stage: ModelVersionStage = ModelVersionStage.NONE
    version_tags: Dict[str, str] = Field(default_factory=dict)
    registry_metadata: Dict[str, str] = Field(default_factory=dict)
    zenml_metadata: Optional[ZenMLModelMetadata] = Field(
        default_factory=ZenMLModelMetadata
    )

    @root_validator
    def fill_in_out_zenml_metadata(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fills in ZenML metadata if not provided.

        Args:
            values: The values to validate.

        Returns:
            The validated values.
        """
        if values.get("zenml_metadata") is None:
            values["zenml_metadata"] = ZenMLModelMetadata()
        version_tags = values.get("version_tags")
        if version_tags:
            if "zenml_version" in version_tags.keys():
                values["zenml_metadata"].zenml_version = version_tags[
                    "zenml_version"
                ]
                values["version_tags"].pop("zenml_version")
            if "zenml_pipeline_run_id" in version_tags.keys():
                values["zenml_metadata"].zenml_pipeline_run_id = version_tags[
                    "zenml_pipeline_run_id"
                ]
                values["version_tags"].pop("zenml_pipeline_run_id")
            if "zenml_pipeline_name" in version_tags.keys():
                values["zenml_metadata"].zenml_pipeline_name = version_tags[
                    "zenml_pipeline_name"
                ]
                values["version_tags"].pop("zenml_pipeline_name")
            if "zenml_step_name" in version_tags.keys():
                values["zenml_metadata"].zenml_step_name = version_tags[
                    "zenml_step_name"
                ]
                values["version_tags"].pop("zenml_step_name")
        return values


class BaseModelRegistryConfig(StackComponentConfig):
    """Base config for model registries."""


class BaseModelRegistry(StackComponent, ABC):
    """Base class for all ZenML model registries."""

    @property
    def config(self) -> BaseModelRegistryConfig:
        """Returns the config of the model registries.

        Returns:
            The config of the model registries.
        """
        return cast(BaseModelRegistryConfig, self._config)

    # ---------
    # Model Registration Methods
    # ---------

    @abstractmethod
    def register_model(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> ModelRegistration:
        """Registers a model in the model registry.

        Args:
            name: The name of the registered model.
            description: The description of the registered model.
            tags: The tags associated with the registered model.
        """

    @abstractmethod
    def delete_model(
        self,
        name: str,
    ) -> None:
        """Deletes a registered model from the model registry.

        Args:
            name: The name of the registered model.
        """

    @abstractmethod
    def update_model(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> ModelRegistration:
        """Updates a registered model in the model registry.

        Args:
            name: The name of the registered model.
            description: The description of the registered model.
            tags: The tags associated with the registered model.
        """

    @abstractmethod
    def get_model(self, name: str) -> ModelRegistration:
        """Gets a registered model from the model registry.

        Args:
            name: The name of the registered model.

        Returns:
            The registered model.
        """

    @abstractmethod
    def list_models(
        self,
        name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[ModelRegistration]:
        """Lists all registered models in the model registry.

        Args:
            name: The name of the registered model.
            tags: The tags associated with the registered model.

        Returns:
            A list of registered models.
        """

    @abstractmethod
    def check_model_exists(self, name: str) -> bool:
        """Checks if a model exists in the model registry.

        Args:
            name: The name of the registered model.

        Returns:
            True if the model exists, False otherwise.
        """

    # ---------
    # Model Version Methods
    # ---------

    @abstractmethod
    def register_model_version(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        model_source_uri: Optional[str] = None,
        version: Optional[str] = None,
        version_description: Optional[str] = None,
        version_tags: Optional[Dict[str, str]] = None,
        registry_metadata: Optional[Dict[str, str]] = None,
        zenml_version: Optional[str] = None,
        zenml_pipeline_run_id: Optional[str] = None,
        zenml_pipeline_name: Optional[str] = None,
        zenml_step_name: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelVersion:
        """Registers a model version in the model registry.

        Args:
            name: The name of the registered model.
            description: The description of the registered
                model.
            tags: The tags associated with the registered
                model.
            model_source_uri: The source URI of the model.
            version: The version of the model version.
            version_description: The description of the model version.
            version_tags: The tags associated with the model version.
            registry_metadata: The metadata associated with the model
                version.
            zenml_version: The ZenML version of the model version.
            zenml_pipeline_run_id: The ZenML pipeline run ID of the model
                version.
            zenml_pipeline_name: The ZenML pipeline run name of the model
                version.
            zenml_step_name: The ZenML step name of the model version.
            **kwargs: Additional keyword arguments.

        Returns:
            The registered model version.
        """

    @abstractmethod
    def delete_model_version(
        self,
        name: str,
        version: str,
    ) -> None:
        """Deletes a model version from the model registry.

        Args:
            name: The name of the registered model.
            version: The version of the model version to delete.
        """

    @abstractmethod
    def update_model_version(
        self,
        name: str,
        version: str,
        version_description: Optional[str] = None,
        version_tags: Optional[Dict[str, str]] = None,
        version_stage: Optional[ModelVersionStage] = None,
    ) -> ModelVersion:
        """Updates a model version in the model registry.

        Args:
            name: The name of the registered model.
            version: The version of the model version to update.
            version_description: The description of the model version.
            version_tags: The tags associated with the model version.
            version_stage: The stage of the model version.

        Returns:
            The updated model version.
        """

    @abstractmethod
    def list_model_versions(
        self,
        name: Optional[str] = None,
        model_source_uri: Optional[str] = None,
        version_tags: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> List[ModelVersion]:
        """Lists all model versions for a registered model.

        Args:
            name: The name of the registered model.
            model_source_uri: The model source URI of the registered model.
            version_tags: The tags associated with the registered model.
            kwargs: Additional keyword arguments.

        Returns:
            A list of model versions.
        """

    @abstractmethod
    def get_model_version(self, name: str, version: str) -> ModelVersion:
        """Gets a model version for a registered model.

        Args:
            name: The name of the registered model.
            version: The version of the model version to get.

        Returns:
            The model version.
        """

    @abstractmethod
    def check_model_version_exists(
        self,
        name: str,
        version: str,
    ) -> bool:
        """Checks if a model version exists in the model registry.

        Args:
            name: The name of the registered model.
            version: The version of the model version to check.

        Returns:
            True if the model version exists, False otherwise.
        """

    @abstractmethod
    def load_model_version(
        self,
        name: str,
        version: str,
        **kwargs: Any,
    ) -> Any:
        """Loads a model version from the model registry.

        Args:
            name: The name of the registered model.
            version: The version of the model version to load.
            **kwargs: Additional keyword arguments.

        Returns:
            The loaded model version.
        """


class BaseModelRegistryFlavor(Flavor):
    """Base class for all ZenML model registry flavors."""

    @property
    def type(self) -> StackComponentType:
        """Type of the flavor.

        Returns:
            StackComponentType: The type of the flavor.
        """
        return StackComponentType.MODEL_REGISTRY

    @property
    def config_class(self) -> Type[BaseModelRegistryConfig]:
        """Config class for this flavor.

        Returns:
            The config class for this flavor.
        """
        return BaseModelRegistryConfig

    @property
    @abstractmethod
    def implementation_class(self) -> Type[StackComponent]:
        """Returns the implementation class for this flavor.

        Returns:
            The implementation class for this flavor.
        """
        return BaseModelRegistry
