from django import template
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_app
# from django.template.loader_tags import ConstantIncludeNode, IncludeNode
from django.template.loader_tags import IncludeNode

register = template.Library()

def do_include_ifapp(parser, token):
    """
    Loads a template and renders it with the current context if the specified
    application is in settings.INSTALLED_APPS.

    Example::

        {% includeifapp app_label "foo/some_include" %}
    """
    bits = token.split_contents()
    if len(bits) != 3:
        raise TemplateSyntaxError, "%r tag takes two argument: the application label and the name of the template to be included" % bits[0]

    app_name, path = bits[1:]
    app_name = app_name.strip('"\'')
    try:
        models = get_app(app_name)
    except ImproperlyConfigured:
        return template.Node()

    # if path[0] in ('"', "'") and path[-1] == path[0]:
    #     return ConstantIncludeNode(path[1:-1])

    return IncludeNode(path)
register.tag('includeifapp', do_include_ifapp)
