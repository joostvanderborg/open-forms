"""
Expose template functionality as public API.

The ``template`` package provides generic template rendering constructs. Features are:

* Option to sandbox templates to only allow safe-ish public API
* Utilities to evaluate templates from string (user-contributed content and inherently
  unsafe).

Possible future features:

* Caching for string-based templates
* ...
"""
from .backends.sandboxed_django import backend as sandbox_backend

__all__ = ["render_from_string", "parse", "sandbox_backend"]


def parse(source: str, backend=sandbox_backend):
    """
    Parse the template fragment using the specified backend.

    :returns: A template instance of the specified backend
    :raises: :class:`django.template.TemplateSyntaxError` if there are any
      syntax errors
    """
    return backend.from_string(source)


def render_from_string(source: str, context: dict, backend=sandbox_backend) -> str:
    """
    Render a template source string using the provided context.

    :arg source: The template source to render
    :arg context: The context data for the template to render
    :arg backend: An optional alternative Django template backend instance to use.
      Defaults to the sandboxed backend.
    :raises: :class:`django.template.TemplateSyntaxError` if the template source is
      invalid
    """
    template = parse(source, backend=backend)
    return template.render(context)
