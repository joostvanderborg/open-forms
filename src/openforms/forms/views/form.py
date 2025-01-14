import logging

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator

from openforms.config.models import GlobalConfiguration
from openforms.ui.views.generic import UIDetailView, UIListView
from openforms.utils.decorators import conditional_search_engine_index

from ..models import Form

logger = logging.getLogger(__name__)


class FormListView(UIListView):
    template_name = "core/views/form/form_list.html"
    queryset = Form.objects.live()

    def get(self, request, *args, **kwargs):
        config = GlobalConfiguration.get_solo()

        if request.user.is_staff:
            return super().get(request, *args, **kwargs)
        elif not config.main_website:
            raise PermissionDenied()
        else:
            # looks like an "open redirect", but admins control the value of this and
            # we only give access to trusted users to the admin.
            return HttpResponseRedirect(config.main_website)


@method_decorator(
    conditional_search_engine_index(config_attr="allow_indexing_form_detail"),
    name="dispatch",
)
class FormDetailView(UIDetailView):
    template_name = "core/views/form/form_detail.html"
    queryset = Form.objects.live()
