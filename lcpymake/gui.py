import time
from time import sleep
import curses
from enum import Enum, auto

from lcpymake import model


class MyColorEnum(Enum):
    RESERVED = 0
    BG = auto()
    MISSING_SOURCE = auto()
    CURSOR = auto()


class MyColor:
    def __init__(self, index, fg, bg):
        curses.init_pair(index, fg, bg)


MyColors = {}


def init_colors(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    stdscr.bkgd(' ', curses.color_pair(MyColorEnum.BG.value) | curses.A_BOLD)
    # stdscr.bkgd(' ', curses.color_pair(Colormap.bg) | curses.A_BOLD | curses.A_REVERSE)


def set_my_colors():
    curses.init_pair(MyColorEnum.BG.value, -1, 44)
    curses.init_pair(MyColorEnum.MISSING_SOURCE.value, 23, -1)
    curses.init_pair(MyColorEnum.CURSOR.value, 20, 200)


def _show_colors(stdscr):
    init_colors(stdscr)
    curses.curs_set(0)  # Hide the cursor
    stdscr.addstr(0, 0, f"{curses.COLOR_PAIRS}")
    try:
        for i in range(0, 255):
            row = i // 10
            col = i - row * 10
            stdscr.addstr(row + 5, 0, f"{row * 10:003}")
            stdscr.addstr(row + 5, col * 4 + 10, f"{i:003}", curses.color_pair(i))
    except Exception:
        # End of screen reached
        pass
    stdscr.getch()


count = 0

current = "none"
hide_construction_command = False
cursor_tree_offset = 0
cursor_tree_points_to = None
max_depth = 3


def splash(screen):
    global count
    global current
    chars = ".oOo..................................."
    c = chars[count % len(chars)]
    screen.addstr(0, 0, c)
    count += 1
    screen.addstr(0, 10, current)


def help(screen):

    messages = [
        ("h", "this help, press again to return to main screen"),
        ("s", "rescan file dependencies"),
        ("c", "show/hide target construction command"),
        ("t", "show tree"),
        ("q", "quit"),
    ]

    row = 5
    for (a, b) in messages:
        screen.addstr(row, 0, f"{a} : {b}")
        row += 1


def print_tree(screen, g):
    first_row = 5
    row = first_row
    global hide_construction_command
    global cursor_tree_offset
    global cursor_tree_points_to
    global max_depth

    if cursor_tree_offset is None:
        cursor_tree_offset = 0
    if cursor_tree_offset < 0:
        cursor_tree_offset = 0

    def print_tree(row, indent, node):
        if indent >= max_depth:
            return row
        col = 3
        # status = node.status
        text = f"{'...' * indent}{node.label}"
        screen.addstr(row, col, text)
        row += 1
        if not node.is_source and not hide_construction_command:
            text = f"{'...' * (indent + 1)}{node.rule_info}"
            screen.addstr(row, col, text)
            row += 1
        else:
            for fdep in node.deps_in_srcdir:
                text = f"{'...' * (indent + 1)}{fdep}"
                screen.addstr(row, col, text)
                row += 1

        for (_, source) in node.sources:
            source_node = g._find_node(source)
            row = print_tree(row, indent + 1, source_node)
        return row

    for node in g._leaf_nodes():
        row = print_tree(row, 0, node)

    row += 1
    screen.addstr(row, 0, f"{len(g.nodes)} nodes ")
    row += 1
    screen.addstr(row, 0, f"{len(g._leaf_artefacts())} leaves (source nodes)")
    screen.move(first_row + cursor_tree_offset, 0)


def _main(screen, g: model.World):
    global current
    global hide_construction_command
    global cursor_tree_offset
    global cursor_tree_points_to
    global max_depth

    init_colors(screen)
    # curses.curs_set(0)  # Hide the cursor
    screen.nodelay(True)  # Don't block I/O calls
    set_my_colors()

    while True:
        screen.erase()
        splash(screen)

        screen.addstr(1, 0, f"srcdir  : {g.srcdir}")
        screen.addstr(2, 0, f"sandbox : {g.sandbox}")

        info = f"max-depth:{max_depth}"
        screen.addstr(0, 20, info)

        command = screen.getch()
        screen.addstr(0, 50, str(command))
        if command != -1:
            if command == ord('h'):
                current = "help"
            elif command == ord('t'):
                current = "tree"
            elif command == ord('c'):
                hide_construction_command = not hide_construction_command
            elif command == ord('s'):
                g._scan()
            elif command == ord('-') and max_depth > 0:
                max_depth -= 1
            elif command == ord('+') and max_depth < 10:
                max_depth += 1
            elif command == curses.KEY_UP:
                cursor_tree_offset -= 1
            elif command == curses.KEY_DOWN:
                cursor_tree_offset += 1
            elif command == ord('q'):
                exit(0)
            else:
                print("unknown command")

        if current == 'help':
            help(screen)
        elif current == 'tree':
            print_tree(screen, g)
        else:
            print_tree(screen, g)

        screen.refresh()
        time.sleep(0.1)


def main(g):
    curses.wrapper(_main, g)


def show_colors():
    curses.wrapper(_show_colors)


if __name__ == "__main__":
    show_colors()
