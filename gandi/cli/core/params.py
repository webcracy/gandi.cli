import click
from click.decorators import _param_memo

from gandi.cli.core.base import GandiContextHelper


class DatacenterParamType(click.Choice):
    name = 'datacenter'

    def __init__(self):
        gandi = GandiContextHelper()
        choices = [item['iso'] for item in gandi.datacenter.list()]
        self.choices = choices

    def convert(self, value, param, ctx):
        value = value.upper()
        return click.Choice.convert(self, value, param, ctx)


class PaasTypeParamType(click.Choice):
    name = 'paas type'

    def __init__(self):
        gandi = GandiContextHelper()
        choices = [item['name'] for item in gandi.paas.type_list()]
        self.choices = choices


class IntChoice(click.Choice):
    name = 'integer choice'

    def get_metavar(self, param):
        return '[%s]' % '|'.join(str(x) for x in self.choices)


class DiskImageParamType(click.Choice):
    name = 'images'

    def __init__(self):
        gandi = GandiContextHelper()
        choices = [item['label'] for item in gandi.image.list()]
        self.choices = choices

DATACENTER = DatacenterParamType()
PAAS_TYPE = PaasTypeParamType()
DISK_IMAGE = DiskImageParamType()


class GandiOption(click.Option):

    def display_value(self, ctx, value):
        gandi = ctx.obj
        gandi.echo('%s: %s' % (self.name, (value if value is not None
                                           else 'Not found')))

    def get_default(self, ctx):
        value = click.Option.get_default(self, ctx)
        if not self.prompt:
            # value found in default display it
            self.display_value(ctx, value)
        return value

    def consume_value(self, ctx, opts):
        value = click.Option.consume_value(self, ctx, opts)
        if not value:
            # value not found by click on command line
            # now check using our context helper in order into
            # local configuration
            # global configuration
            gandi = ctx.obj
            value = gandi.get(self.name)
            if value is not None:
                # value found in configuration display it
                self.display_value(ctx, value)

        return value

    def handle_parse_result(self, ctx, opts, args):
        value = self.consume_value(ctx, opts)
        value = self.full_process_value(ctx, value)
        if self.callback is not None:
            value = self.callback(ctx, value)
        if self.expose_value:
            ctx.params[self.name] = value
        if value is not None:
            # save to gandi configuration
            gandi = ctx.obj
            gandi.configure(True, self.name, value)
        return value, args


def option(*param_decls, **attrs):
    """Attaches an option to the command.  All positional arguments are
    passed as parameter declarations to :class:`Option`, all keyword
    arguments are forwarded unchanged.  This is equivalent to creating an
    :class:`Option` instance manually and attaching it to the
    :attr:`Command.params` list.
    """
    def decorator(f):
        _param_memo(f, GandiOption(param_decls, **attrs))
        return f
    return decorator

# create a decorator to pass the Gandi object as context to click calls
pass_gandi = click.make_pass_decorator(GandiContextHelper)
