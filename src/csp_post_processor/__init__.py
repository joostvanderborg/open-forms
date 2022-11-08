from .processor import bleach_wysiwyg_content, post_process_html

__version__ = "0.1.0"

__all__ = ["bleach_wysiwyg_content", "post_process_html"]

default_app_config = "csp_post_processor.apps.CSPPostProcessConfig"
