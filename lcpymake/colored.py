from functools import lru_cache
import json
from pathlib import Path
# pylint:disable=E0401
from sty import fg, bg, ef, rs
# pylint:enable=E0401

here = Path(__file__).parent
# data_colors = json.loads((here / 'colors.json').read_text())
data_colors = {}


@lru_cache(1)
def rgb_of_color_name(name: str) -> str:
    if name is None:
        return ''
    # pylint:disable=W0120
    for d in data_colors:
        if d['name'] == name:
            return (d['rgb']['r'], d['rgb']['g'], d['rgb']['b'])
    else:
        print(f"color not found : '{name}'")
        return ''
    # pylint:enable=W0120


color_map = {
    'BUILD_UP_TO_DATE': {'fg': 'Green'},
    'SOURCE_PRESENT': {'fg': 'LightGreen'},
    'SOURCE_MISSING': {'fg': 'Red', 'bg': 'White'},
    'BUILT_MISSING': {'fg': 'LightSkyBlue1'},
    'NEEDS_REBUILD': {'fg': 'Purple', 'bold': True},
    'RULE': {'fg': 'Grey'},
    'DEP': {'fg': 'IndianRed'}
}


def colored_string(choice: str, text: str, nocolor: bool) -> str:
    """

    :param node:
    :return:
    """
    if nocolor:
        return text
    text = str(text)
    infos = color_map.get(choice, None)
    if infos is None:
        print(f'no info for choice {choice}')
        return text
    if infos.get('fg') is not None:
        text = fg(*rgb_of_color_name(infos.get('fg'))) + text
    if infos.get('bg') is not None:
        text = bg(*rgb_of_color_name(infos.get('bg'))) + text
    if infos.get('bold', False):
        text = ef.bold + text

    return text + bg.rs + fg.rs + rs.bold_dim
