import logging
import warnings
from typing import Any, Dict, Iterator, List, Optional, Tuple

import elasticapm
from glom import glom

from openforms.variables.constants import DEFAULT_INITIAL_VALUE, FormVariableDataTypes

from ..typing import DataMapping, JSONObject
from .constants import COMPONENT_DATATYPES
from .typing import Component

logger = logging.getLogger(__name__)


@elasticapm.capture_span(span_type="app.formio.configuration")
def iter_components(
    configuration: JSONObject, recursive=True, _is_root=True, _mark_root=False
) -> Iterator[Component]:
    components = configuration.get("components")
    if configuration.get("type") == "columns" and recursive:
        assert not components, "Both nested components and columns found"
        for column in configuration["columns"]:
            yield from iter_components(
                configuration=column, recursive=recursive, _is_root=False
            )

    if components:
        for component in components:
            if _mark_root:
                component["_is_root"] = _is_root
            yield component
            if recursive:
                yield from iter_components(
                    configuration=component, recursive=recursive, _is_root=False
                )


@elasticapm.capture_span(span_type="app.formio.configuration")
def get_component(configuration: JSONObject, key: str) -> Optional[Component]:
    warnings.warn(
        "`openforms.formio.utils.get_component` is not efficient, use "
        "`openforms.formio.utils.FormioConfigurationWrapper` instead.",
        DeprecationWarning,
    )
    for component in iter_components(configuration=configuration, recursive=True):
        if component["key"] == key:
            return component


@elasticapm.capture_span(span_type="app.formio.configuration")
def flatten_by_path(configuration: JSONObject) -> Dict[str, Component]:
    """
    Flatten the formio configuration.

    Takes a (nested) Formio configuration object and flattens it, using the full
    JSON path as key and the component as value in the returned mapping.
    """

    def _generator(
        _configuration: JSONObject, prefix: str = "components"
    ) -> Iterator[Tuple[str, Component]]:
        for index, component in enumerate(
            iter_components(_configuration, recursive=False)
        ):
            full_path = f"{prefix}.{index}"
            yield full_path, component

            # could be a component, could be something else
            has_components = "components" in component
            has_columns = "columns" in component

            if has_columns:
                for col_index, column in enumerate(component["columns"]):
                    nested_prefix = f"{full_path}.columns.{col_index}.components"
                    yield from _generator(column, prefix=nested_prefix)
            elif has_components:
                yield from _generator(component, prefix=f"{full_path}.components")

    result = dict(_generator(configuration))
    return result


def is_layout_component(component):
    # Adapted from isLayoutComponent util function in Formio
    # https://github.com/formio/formio.js/blob/4.13.x/src/utils/formUtils.js#L25
    column = component.get("columns")
    components = component.get("components")
    rows = component.get("rows")

    if (
        (column and isinstance(column, list))
        or (components and isinstance(components, list))
        or (rows and isinstance(rows, list))
    ):
        return True

    return False


def component_in_editgrid(configuration: dict, component: dict) -> bool:
    # Get all the editgrid components in the configuration
    editgrids = []
    for comp in iter_components(configuration=configuration):
        if comp["type"] == "editgrid":
            editgrids.append(comp)

    # Check if the component is in the editgrid
    for editgrid in editgrids:
        for comp in iter_components(configuration=editgrid):
            if comp["key"] == component["key"]:
                return True

    return False


def get_component_datatype(component):
    component_type = component["type"]
    if component.get("multiple"):
        return FormVariableDataTypes.array
    return COMPONENT_DATATYPES.get(component_type, FormVariableDataTypes.string)


def get_component_empty_value(component):
    data_type = get_component_datatype(component)

    return DEFAULT_INITIAL_VALUE.get(data_type, "")


def get_component_default_value(component) -> Optional[Any]:
    # Formio has a getter for the:
    # - emptyValue: https://github.com/formio/formio.js/blob/4.13.x/src/components/textfield/TextField.js#L58
    # - defaultValue:
    #    https://github.com/formio/formio.js/blob/4.13.x/src/components/_classes/component/Component.js#L2302
    # If the defaultValue is empty, then the field will be populated with the emptyValue in the form data.
    default_value = component.get("defaultValue")
    if component.get("multiple") and default_value is None:
        return []
    return default_value


# See https://help.form.io/userguide/forms/form-components#input-mask for the
# semantics, and FormioUtils.getInputMask for the implementation.
def conform_to_mask(value: str, mask: str) -> str:
    """
    Given an input and a Formio mask, try to conform the value to the mask.

    If the value is not compatible with the mask, a ``ValueError`` is raised.
    """
    # loop through all the characters of the value and test them against the mask. Note
    # that the value and mask may have different lengths due to non-input characters
    # such as spaces/dashes... Formio only recognizes alphanumeric inputs as variable
    # user input, the rest is part of the mask.
    # NOTE: we don't check for numeric masks or not, let that be handled by Formio itself

    # the final result characters, build from the value and mask
    result: List[str] = []
    char_index, mask_index = 0, 0
    LOOP_GUARD, iterations = 1000, 0

    # maps the formio mask characters to rules to test for alphanumeric chars etc.
    TEST_RULES = {
        "9": lambda c: c.isnumeric(),
        "A": lambda c: c.isalpha(),
        "a": lambda c: c.isalpha(),
        "*": lambda c: c.isalnum(),
    }

    # the loop indices are reset within an iteration, but in the end either a ValueError
    # is raised because of mismatch with the mask, or the value has been re-formatted
    # conforming to the mask and thus has the same length.
    while len(result) != len(mask):
        if iterations > LOOP_GUARD:  # pragma: nocover
            raise RuntimeError("Infinite while-loop detected!")
        iterations += 1

        try:
            char, mask_char = value[char_index], mask[mask_index]
        except IndexError as exc:
            raise ValueError("Ran out of mask or value characters to process") from exc

        test = TEST_RULES.get(mask_char)

        # check if the character matches the mask - if it does, post-process and put
        # it in the result list
        if test and test(char) is True:
            # check if we need to allow uppercase
            if mask_char.islower() and char.isupper():
                char = char.lower()
            result.append(char)
            # at the end of processing a character, advance the indices for the next
            # character
            char_index += 1
            mask_index += 1
            continue
        elif char == mask_char:  # literal match -> good to go
            result.append(char)
            # at the end of processing a character, advance the indices for the next
            # character
            char_index += 1
            mask_index += 1
            continue
        elif test is not None:  # there is a test, but it didn't pass
            # there was a test, meaning this is an alphanumeric mask of some form. We
            # may potentially skip some separator/formatting chars but ONLY if the
            # current char is not alphanumeric at all. If it is, it doesn't match
            # the expected pattern and we raise a ValueError.
            if char.isalnum():
                raise ValueError(
                    f"Character {char} did not match expected pattern {mask_char}"
                )
            elif mask_char == "*":
                raise ValueError(f"Character {char} was expected to be alphanumeric")
            # at the end of processing a character, advance the indices for the next
            # character
            char_index += 1
            continue
        elif test is None:  # no test -> it's a formatting character
            # if we encounter a formatting character that isn't the current input character,
            # check if the current character is possibly an input (by checking if it's
            # alphanumeric). If it's not, then we have a mismatch, otherwise we insert
            # the formatting character in the result list and process the char again
            # against the next mask char.
            if not char.isalnum():
                raise ValueError(
                    f"Character {char} did not match expected formatting character {mask_char}"
                )

            # the character is probably input, so add the formatter to the result list and
            # keep the current char_index so that we process it again
            result.append(mask_char)
            mask_index += 1
            continue

        else:  # pragma: nocover
            raise RuntimeError(
                f"Unexpected situation! Mask: {mask}, input value: {value}"
            )

    return "".join(result)


def is_visible_in_frontend(component: JSONObject, data: DataMapping) -> bool:
    """Check if the component is visible because of frontend logic

    The rules in formio are expressed as:

    .. code-block:: json

        {
            "show": true/false,
            "when": <key of trigger component>,
            "eq": <compare value>
        }

    """
    hidden = component.get("hidden")
    conditional = component.get("conditional")

    if not conditional or (conditional_show := conditional.get("show")) is None:
        return not hidden

    trigger_component_key = conditional.get("when")
    trigger_component_value = glom(data, trigger_component_key, default=None)
    compare_value = conditional.get("eq")

    return (
        conditional_show
        if trigger_component_value == compare_value
        else not conditional_show
    )
