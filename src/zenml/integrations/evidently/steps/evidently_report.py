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
"""Implementation of the Evidently Report Step."""

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast

import pandas as pd
from evidently.pipeline.column_mapping import (  # type: ignore[import]
    ColumnMapping,
)
from pydantic import BaseModel, Field

from zenml.integrations.evidently.data_validators import EvidentlyDataValidator
from zenml.steps import Output
from zenml.steps.base_parameters import BaseParameters
from zenml.steps.base_step import BaseStep


class EvidentlyColumnMapping(BaseModel):
    """Column mapping configuration for Evidently.

    This class is a 1-to-1 serializable analog of Evidently's
    ColumnMapping data type that can be used as a step configuration field
    (see https://docs.evidentlyai.com/user-guide/input-data/column-mapping).

    Attributes:
        target: target column
        prediction: target column
        datetime: datetime column
        id: id column
        numerical_features: numerical features
        categorical_features: categorical features
        datetime_features: datetime features
        target_names: target column names
        task: model task
        pos_label: positive label
        text_features: text features
    """

    target: Optional[str] = None
    prediction: Optional[Union[str, Sequence[str]]] = "prediction"
    datetime: Optional[str] = None
    id: Optional[str] = None
    numerical_features: Optional[List[str]] = None
    categorical_features: Optional[List[str]] = None
    datetime_features: Optional[List[str]] = None
    target_names: Optional[List[str]] = None
    task: Optional[str] = None
    pos_label: Optional[Union[str, int]] = 1
    text_features: Optional[List[str]] = None

    def to_evidently_column_mapping(self) -> ColumnMapping:
        """Convert this Pydantic object to an Evidently ColumnMapping object.

        Returns:
            An Evidently column mapping converted from this Pydantic object.
        """
        column_mapping = ColumnMapping()

        # preserve the Evidently defaults where possible
        column_mapping.target = self.target or column_mapping.target
        column_mapping.prediction = (
            self.prediction or column_mapping.prediction
        )
        column_mapping.datetime = self.datetime or column_mapping.datetime
        column_mapping.id = self.id or column_mapping.id
        column_mapping.numerical_features = (
            self.numerical_features or column_mapping.numerical_features
        )
        column_mapping.datetime_features = (
            self.datetime_features or column_mapping.datetime_features
        )
        column_mapping.target_names = (
            self.target_names or column_mapping.target_names
        )
        column_mapping.task = self.task or column_mapping.task
        column_mapping.pos_label = self.pos_label or column_mapping.pos_label
        column_mapping.text_features = (
            self.text_features or column_mapping.text_features
        )

        return column_mapping


class EvidentlyReportParameters(BaseParameters):
    """Parameters class for Evidently profile steps.

    Attributes:
        column_mapping: properties of the DataFrame columns used
        ignored_cols: columns to ignore during the Evidently report step
        metrics: a list of metrics, metrics presets or a dictionary of
            metrics to use with the gnerate_column_metrics method.

            The metrics and the metric presets should be strings with the exact
            names as in the evidently library. The dictionary should be used when
            you want to choose a metric for more than one columns. The structure
            of the dictionary should be as follows:
            {
                "metric": "metric_name",
                "parameters": {},
                "columns": ["column1", "column2"]
            }

        report_options: a list of tuples containing the name of the report
            and a dictionary of options for the report.
    """

    column_mapping: Optional[EvidentlyColumnMapping] = None
    ignored_cols: Optional[List[str]] = None
    metrics: List[Union[str, Dict[str, Any]]] = None
    report_options: Sequence[Tuple[str, Dict[str, Any]]] = Field(
        default_factory=list
    )

    class Config:
        """Pydantic config class."""

        arbitrary_types_allowed = True


class EvidentlyReportStep(BaseStep):
    """Step implementation implementing an Evidently Report Step."""

    def entrypoint(
        self,
        reference_dataset: pd.DataFrame,
        comparison_dataset: pd.DataFrame,
        params: EvidentlyReportParameters,
    ) -> Output(  # type:ignore[valid-type]
        report_json=str, report_html=str
    ):
        """Main entrypoint for the Evidently report step.

        Args:
            reference_dataset: a Pandas DataFrame
            comparison_dataset: a Pandas DataFrame of new data you wish to
                compare against the reference data
            params: the parameters for the step

        Raises:
            ValueError: If ignored_cols is an empty list
            ValueError: If column is not found in reference or comparison
                dataset

        Returns:
            A tuple containing the Evidently report in JSON and HTML
        """
        data_validator = cast(
            EvidentlyDataValidator,
            EvidentlyDataValidator.get_active_data_validator(),
        )
        column_mapping = None

        if params.ignored_cols is None:
            pass

        elif not params.ignored_cols:
            raise ValueError(
                f"Expects None or list of columns in strings, but got {params.ignored_cols}"
            )

        elif not (
            set(params.ignored_cols).issubset(set(reference_dataset.columns))
        ) or not (
            set(params.ignored_cols).issubset(set(comparison_dataset.columns))
        ):
            raise ValueError(
                "Column is not found in reference or comparison datasets"
            )

        else:
            reference_dataset = reference_dataset.drop(
                labels=list(params.ignored_cols), axis=1
            )
            comparison_dataset = comparison_dataset.drop(
                labels=list(params.ignored_cols), axis=1
            )

        if params.column_mapping:
            column_mapping = (
                params.column_mapping.to_evidently_column_mapping()
            )
        report = data_validator.data_profiling(
            dataset=reference_dataset,
            comparison_dataset=comparison_dataset,
            metric_list=params.metrics,
            column_mapping=column_mapping,
            report_options=params.report_options,
        )
        return [report.json(), report.show().data]


def evidently_report_step(
    step_name: str,
    params: EvidentlyReportParameters,
) -> BaseStep:
    """Shortcut function to create a new instance of the EvidentlyReportStep.

    The returned EvidentlyReportStep can be used in a pipeline to
    run model drift analyses on two input pd.DataFrame datasets and return the
    results as an Evidently Report object in JSON and HTML formats.

    Args:
        step_name: The name of the step
        params: The parameters for the step

    Returns:
        a EvidentlyReportStep step instance
    """
    return EvidentlyReportStep(name=step_name, params=params)