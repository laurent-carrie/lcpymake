import sys
from pathlib import Path
# pylint:disable=E0401
import click
# pylint:enable=E0401
from lcpymake import model, base
from lcpymake.gui import main as main_gui

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
@click.option('--no-color', 'nocolor_', required=False, default=False, is_flag=True,
              help='print graph without color (useful when redirecting to a file)')
@click.option('--gui', required=False, default=False, is_flag=True,
              help='run interactive gui (requires curses)')
def main(script, print_, build_, mount_, nocolor_, gui):
    print(f'hello world {script}')
    sys.path.append(str(Path(script).absolute().parent))
    exec(f"from {str(Path(script).with_suffix('').name)} import main as client_main")

    try:
        g = eval('client_main()')
    except (base.NoSuchNode) as e:
        click.echo(click.style(str(type(e)), bg='red', fg='black'))
        click.echo(click.style(str(e), bg='red', fg='black'))
        sys.exit(1)

    if not isinstance(g, model.World):
        raise ValueError(
            f'user function main does not return the expected type, it returns {type(g)}')

    if gui:
        main_gui(g)
        exit(0)

    click.echo('srcdir  : ', nl=False)
    click.echo(click.style(str(g.srcdir), bg='blue', fg='white'))
    click.echo('sandbox : ', nl=False)
    click.echo(click.style(str(g.sandbox), bg='blue', fg='white'))

    if print_:
        g._scan()
        g._print(nocolor_)

    if mount_:
        g._mount(allow_missing=True)

    if build_:
        try:
            g._mount(allow_missing=False)
            g._build()
        except (base.SourceFileMissing, base.RuleFailed) as e:
            click.echo(click.style(str(type(e)), bg='red', fg='black'))
            click.echo(click.style(str(e), bg='red', fg='black'))
