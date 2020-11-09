import sys
from pathlib import Path
# pylint:disable=E0401
import click
# pylint:enable=E0401

from lcpymake import model

# pylint:disable=W0122
# pylint:disable=W0123
# pylint:disable=W0212


@click.command()
@click.option('--print', 'print_', required=False, default=False, is_flag=True,
              help='print build tree')
@click.option('--script', required=True, type=str,
              help='python script to build graph')
@click.option('--mount', 'mount_', required=False, default=False, is_flag=True,
              help='mount source files into sandbox')
@click.option('--build', 'build_', required=False, default=False, is_flag=True,
              help='run a build')
def main(script, print_, build_, mount_):
    print(f'hello world {script}')
    sys.path.append(str(Path(script).absolute().parent))
    exec(f"from {str(Path(script).with_suffix('').name)} import main as client_main")

    try:
        g: model.World = eval('client_main()')
    except (model.NoSuchNode) as e:
        click.echo(click.style(str(type(e)), bg='red', fg='black'))
        click.echo(click.style(str(e), bg='red', fg='black'))
        sys.exit(1)

    if not isinstance(g, model.World):
        raise ValueError(
            f'user function main does not return the expected type, it returns {type(g)}')

    click.echo('srcdir  : ', nl=False)
    click.echo(click.style(str(g.srcdir), bg='blue', fg='white'))
    click.echo('sandbox : ', nl=False)
    click.echo(click.style(str(g.sandbox), bg='blue', fg='white'))

    if print_:
        g._scan()
        g._print()

    if mount_:
        g._mount(allow_missing=True)

    if build_:
        try:
            g._mount(allow_missing=False)
            g._build()
        except (model.SourceFileMissing, model.RuleFailed) as e:
            click.echo(click.style(str(type(e)), bg='red', fg='black'))
            click.echo(click.style(str(e), bg='red', fg='black'))
