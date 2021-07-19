from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.plugins.api.serializers import PluginBaseSerializer


class RegistrationPluginSerializer(PluginBaseSerializer):
    pass


@dataclass
class ChoiceWrapper:
    choice: tuple

    def __post_init__(self):
        self.value = self.choice[0]
        self.label = self.choice[1]


class RegistrationAttributeSerializer(serializers.Serializer):
    id = serializers.CharField(
        source="value",
        label=_("ID"),
        help_text=_("The unique attribute identifier"),
    )
    label = serializers.CharField(
        label=_("Label"),
        help_text=_("The human-readable name for an attribute."),
    )