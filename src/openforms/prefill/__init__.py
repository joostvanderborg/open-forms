"""
This package holds the base module structure for the pre-fill plugins used in Open Forms.

Various sources exist that can be consulted to fetch data for an active session,
where the BSN, CoC number... can be used to retrieve this data. Think of pre-filling
the address details of a person after logging in with DigiD.

The package integrates with the form builder such that it's possible for every form
field to select which pre-fill plugin to use and which value to use from the fetched
result. Plugins can be registered using a similar approach to the registrations
package. Each plugin is responsible for exposing which attributes/data fragments are
available, and for performing the actual look-up. Plugins receive the
:class:`openforms.submissions.models.Submission` instance that represents the current
form session of an end-user.

Prefill values are embedded as default values for form fields, dynamically for every
user session using the component rewrite functionality in the serializers.

So, to recap:

1. Plugins are defined and registered
2. When editing form definitions in the admin, content editors can opt-in to pre-fill
   functionality. They select the desired plugin, and then the desired attribute from
   that plugin.
3. End-user starts the form and logs in, thereby creating a session/``Submission``
4. The submission-specific form definition configuration is enhanced with the pre-filled
   form field default values.

.. todo:: Move the public API into ``openforms.prefill.service``.

"""
import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import elasticapm
from glom import Path, PathAccessError, glom
from zgw_consumers.concurrent import parallel

from openforms.plugins.exceptions import PluginNotEnabled

if TYPE_CHECKING:  # pragma: nocover
    from openforms.formio.service import FormioConfigurationWrapper
    from openforms.submissions.models import Submission

logger = logging.getLogger(__name__)


@elasticapm.capture_span(span_type="app.prefill")
def _fetch_prefill_values(
    grouped_fields: Dict[str, list], submission: "Submission", register
) -> Dict[str, Dict[str, Any]]:
    from openforms.logging import (  # local import to prevent AppRegistryNotReady
        logevent,
    )

    @elasticapm.capture_span(span_type="app.prefill")
    def invoke_plugin(item: Tuple[str, List[str]]) -> Tuple[str, Dict[str, Any]]:
        plugin_id, fields = item
        plugin = register[plugin_id]

        if not plugin.is_enabled:
            raise PluginNotEnabled()

        try:
            values = plugin.get_prefill_values(submission, fields)
            if not values:
                try:
                    raise ValueError(f"Empty values for prefill plugin '{plugin_id}'")
                except ValueError as e:
                    logger.exception(f"exception in prefill plugin '{plugin_id}'")
                    logevent.prefill_retrieve_failure(submission, plugin, e)
                    return plugin_id, values
        except Exception as e:
            logger.exception(f"exception in prefill plugin '{plugin_id}'")
            logevent.prefill_retrieve_failure(submission, plugin, e)
            return plugin_id, {}
        else:
            logevent.prefill_retrieve_success(submission, plugin, fields)
            return plugin_id, values

    with parallel() as executor:
        results = executor.map(invoke_plugin, grouped_fields.items())

    return dict(results)


def inject_prefill(
    configuration_wrapper: "FormioConfigurationWrapper", submission: "Submission"
) -> None:
    """
    Mutates each component found in configuration according to the prefilled values.

    :param configuration_wrapper: The Formiojs JSON schema wrapper describing an entire
      form or an individual component within the form.
    :param submission: The :class:`openforms.submissions.models.Submission` instance
      that holds the values of the prefill data. The prefill data was fetched earlier,
      see :func:`prefill_variables`.

    The prefill values are looped over by key: value, and for each value the matching
    component is looked up to normalize it in the context of the component.
    """
    from openforms.formio.service import normalize_value_for_component

    prefilled_data = submission.get_prefilled_data()
    for key, prefill_value in prefilled_data.items():
        try:
            component = configuration_wrapper[key]
        except KeyError:
            # The component to prefill is not in this step
            continue

        if not (prefill := component.get("prefill")):
            continue
        if not prefill.get("plugin"):
            continue
        if not prefill.get("attribute"):
            continue

        default_value = component.get("defaultValue")
        # 1693: we need to normalize values according to the format expected by the
        # component. For example, (some) prefill plugins return postal codes without
        # space between the digits and the letters.
        prefill_value = normalize_value_for_component(component, prefill_value)

        if prefill_value != default_value and default_value is not None:
            logger.info(
                "Overwriting non-null default value for component %r",
                component,
            )
        component["defaultValue"] = prefill_value


@elasticapm.capture_span(span_type="app.prefill")
def prefill_variables(submission: "Submission", register=None) -> None:
    from .registry import register as default_register

    register = register or default_register

    state = submission.load_submission_value_variables_state()
    variables_to_prefill = state.get_prefill_variables()

    grouped_fields = defaultdict(list)
    for variable in variables_to_prefill:
        grouped_fields[variable.form_variable.prefill_plugin].append(
            variable.form_variable.prefill_attribute
        )

    results = _fetch_prefill_values(grouped_fields, submission, register)

    prefill_data = {}
    for variable in variables_to_prefill:
        try:
            prefill_value = glom(
                results,
                Path(
                    variable.form_variable.prefill_plugin,
                    variable.form_variable.prefill_attribute,
                ),
            )
        except PathAccessError:
            continue
        else:
            prefill_data[variable.key] = prefill_value

    state.save_prefill_data(prefill_data)
