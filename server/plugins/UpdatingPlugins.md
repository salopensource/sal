# Updating old-school Sal Plugins
This document helps you in systematically updating your existing Sal plugins to make use of the new `sal.plugin` module and plugin classes, prior to the deprecation of old-school plugins in a future major version release.

1. `import sal.plugin`
  1. (Do not `from sal.plugin import <anything>`, as this will cause yapsy to have issues.
2. Replace plugin's base class from `IPlugin` to `sal.plugin.Widget`, `sal.plugin.DetailPlugin`, or `sal.plugin.ReportPlugin`.
3. Remove the yapsy import as well as any other imports that aren't actually being used.
4. The new plugin class will automatically use `<pluginname>/templates/<pluginname>.html` for its template. Unless there's no way to use a single template, you can remove the `template` selection and loading from the existing `widget_content` method.
5. `widget_width` and `description` are now class attributes. You can remove these methods.
  1. Set the plugin classes' `description = 'whatever'`
  2. Regular and machine detail plugins have a default width of 4; reports are 12. There's no need to specify widget_width unless you want to change this.
6. Remove the `plugin_type` method. It's no longer used.
7. Rename the `widget_content` method to `get_context`, and change the parameters. The signature should now look like this:
  - `def get_context(self, queryset, **kwargs):`
8. Rename all uses of the previous parameter `machines` to `queryset` in the `get_context` method.
9. Start a context dictionary by calling `context = self.super_get_context(queryset, **kwargs)`. This puts the plugin, `group_type`, and `group_id` key/value pairs into the context for you.
10. Make `get_context` return the context dictionary, not a rendered template.
  1. In a lot of existing plugin code, this means making sure you don't overwrite the context you started in the previous step; insure you're adding values to it, not recreating it.
  2. Django no longer expects a `Context` object be passed to templates, so you can remove that invocation as well as the import of `Context` and `loader`, if present.
11. The queryset passed into `get_context` has already been filtered for Business Unit, Machine Group, "All", so you can remove any code that does that.
12. Likewise, you cam remove any access handling code, as user permissions have already been checked before your plugin code executes.
13. `DetailPlugin` receives a single machine rather than a queryset. Keep that in mind when looking over code.
14. In most cases, the main body of the (now) `get_context` method does not have to be changed.
15. The `filter_machines` method should be renamed to `filter`.
16. Check your templates and update the following
  1. You no longer need to pass a title into the template via context; Use `{{ plugin.title }}` instead.
  2. Likewise, plugins have a repr method now; so you can use `{{ plugin }}` instead of passing a plugin name. The repr method returns the name of the plugin class; for example `MunkiInstalls`. This is the name used in plugin loading / URL construction...
  3. Update all URL constructions.
      1. Most reversed URLs are to list machines. The `machine_list_id` and `machine_list_front` names are deprecated; please update to simply `machine_list`.
    2. The `page` parameter should be replaced with `group_type` (which is already in your context).
    3. The `theid` parameter should be replaced with `group_id` (also in the context).
    4. If your `{% url %}` calls use a passed plugin name, just use the plugin object itself.
    5. Example
      1. Old: `{% url 'machine_list_id' 'MunkiVersion' 'abc123' page theid %}".replace(/abc123/, row['label'].toString());`
      2. New: `{% url 'machine_list' plugin 'abc123' group_type group_id %}".replace(/abc123/, row['label'].toString());`
  4. If you were using different templates for "front" and "id" views, you can use a single template. Observe the auto-template naming rules from earlier, and you can probably use a very lightly modified version of your previous "id" template.
