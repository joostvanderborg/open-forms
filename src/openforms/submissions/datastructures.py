from dataclasses import dataclass, field
from typing import Any, Tuple

from glom import assign

from openforms.typing import DataMapping

from .models.submission_value_variable import SubmissionValueVariablesState


@dataclass
class DataContainer:
    """
    A data container to access the submission variable values as python objects.
    """

    state: SubmissionValueVariablesState

    _initial_data: Tuple[Tuple[str, Any]] = field(init=False, default_factory=tuple)

    def __post_init__(self):
        # ensure the initial data is immutable
        self._initial_data = tuple(self.data.items())  # record for logging purposes

    @property
    def initial_data(self) -> DataMapping:
        return dict(self._initial_data)

    @property
    def data(self) -> DataMapping:
        """
        Collect the total picture of data/variable values.

        The current view on the submission variable value state is augmented with
        the static variables.

        :return: A datamapping (key: variable key, value: variable value) ready for
          (template context) evaluation.
        """
        dynamic_values = {
            key: variable.to_python() for key, variable in self.state.variables.items()
        }
        static_values = self.state.static_data()
        # this construct may have dots in the key names, so we need to expand that
        # into nested objects
        flattened_data = {**dynamic_values, **static_values}
        nested_data = {}
        for dotted_path, value in flattened_data.items():
            assign(nested_data, dotted_path, value, missing=dict)
        return nested_data

    def update(self, updates: DataMapping) -> None:
        """
        Update the dynamic data state.
        """
        self.state.set_values(updates)
