#  Copyright (c) ZenML GmbH 2021. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

import tempfile
from abc import abstractmethod
from typing import Any

import graphviz

from zenml.logger import get_logger
from zenml.post_execution.pipeline_run import PipelineRunView
from zenml.visualizers.base_pipeline_run_visualizer import (
    BasePipelineRunVisualizer,
)

logger = get_logger(__name__)


class PipelineRunDagVisualizer(BasePipelineRunVisualizer):
    """Visualize the lineage of runs in a pipeline."""

    @abstractmethod
    def visualize(
        self, object: PipelineRunView, *args: Any, **kwargs: Any
    ) -> graphviz.Digraph:
        """Creates a pipeline lineage diagram using plotly.

        Args:
            pipeline:
            *args:
            **kwargs:

        Returns:

        """
        dot = graphviz.Digraph(comment=object.name)
        for step in object.steps:
            dot.node(str(step.id), step.name)
            for parent_step_id in step.parents_step_ids:
                dot.edge(str(parent_step_id), str(step.id))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
            dot.render(filename=f.name, view=True)
        return dot
