from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from openforms.forms.models import FormVariable
from openforms.submissions.models import Submission


@dataclass
class BaseStaticVariable(ABC):
    identifier: str
    name: str = field(init=False)
    data_type: str = field(init=False)

    @abstractmethod
    def get_initial_value(self, submission: Optional[Submission] = None):
        raise NotImplementedError()  # pragma: nocover

    def get_static_variable(self, submission: Optional[Submission] = None):
        return FormVariable(
            name=self.name,
            key=self.identifier,
            data_type=self.data_type,
            initial_value=self.get_initial_value(submission=submission),
        )