import time
import curses
from enum import Enum, auto

import lcpymake.world
from lcpymake import logger


class MyColorEnum(Enum):
    RESERVED = 0
    BG = auto()
    RULE = auto()
    CURSOR = auto()
    SOURCE_PRESENT = auto()
    SOURCE_MISSING = auto()
    BUILD_UP_TO_DATE = auto()
    BUILT_MISSING = auto()
    NEEDS_REBUILD = auto()
    SCANNED_MISSING_DEP = auto()
    DIGEST = auto()


def init_colors(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    stdscr.bkgd(' ', curses.color_pair(MyColorEnum.BG.value) | curses.A_BOLD)
    # stdscr.bkgd(' ', curses.color_pair(Colormap.bg) | curses.A_BOLD | curses.A_REVERSE)


def set_my_colors():
    bg = 115
    curses.init_pair(MyColorEnum.BG.value, -1, bg)
    curses.init_pair(MyColorEnum.SOURCE_PRESENT.value, 100, bg)
    curses.init_pair(MyColorEnum.SOURCE_MISSING.value, 23, 100)
    curses.init_pair(MyColorEnum.BUILD_UP_TO_DATE.value, 20, bg)
    curses.init_pair(MyColorEnum.BUILT_MISSING.value, 197, bg)
    curses.init_pair(MyColorEnum.RULE.value, 23, bg)
    curses.init_pair(MyColorEnum.CURSOR.value, 20, 200)
    curses.init_pair(MyColorEnum.NEEDS_REBUILD.value, 165, bg)
    curses.init_pair(MyColorEnum.DIGEST.value, 180, bg)


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

current = "tree"
hide_construction_command = False
hide_deps = False
hide_digest = False
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
    screen.erase()
    screen.refresh()

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

    row = 15
    screen.addstr(row, 0, "color codes : ")
    row += 1
    for data in MyColorEnum:
        screen.addstr(row, 0, str(data.name), curses.color_pair(data.value))
        row += 1

    screen.refresh()


def scan(screen, g):
    logger.info("scan")
    screen.erase()
    screen.addstr(10, 10, "scanning...")
    screen.refresh()
    g._scan()


def build(screen, g):
    screen.erase()
    screen.addstr(10, 10, "build...")
    screen.refresh()
    g._build()


def print_tree(screen, g):
    screen.erase()
    screen.refresh()
    splash(screen)

    first_row = 5
    row = first_row
    global hide_construction_command, hide_deps
    global cursor_tree_offset
    global cursor_tree_points_to
    global max_depth
    global hide_digest

    if cursor_tree_offset is None:
        cursor_tree_offset = 0
    if cursor_tree_offset < 0:
        cursor_tree_offset = 0

    def print_tree(row, indent, node):
        if indent >= max_depth:
            return row
        col = 3
        # status = node.status
        dots = '|--' * (indent) + '@'
        screen.addstr(row, col, dots)
        screen.addstr(row, col + len(dots), node.label,
                      curses.color_pair(MyColorEnum.RULE.value))

        row += 1
        if not node.is_source and not hide_construction_command:
            dots = '|  ' * indent + '|-- Rule: '
            screen.addstr(row, col, dots)
            screen.addstr(row, col + len(dots),
                          "xxx",
                          # node.rule_info[0:curses.COLS - len(dots) - 3],
                          curses.color_pair(MyColorEnum.RULE.value))
            row += 1
        elif not hide_deps:
            # for fdep in node.deps_in_srcdir:
            for fdep in []:
                dots = '|  ' * indent + '|-- Deps: '
                screen.addstr(row, col, dots)
                screen.addstr(row, col + len(dots), str(fdep))
                row += 1

        if not hide_digest:
            dots = '|  ' * indent + '|-- Digest A: '
            screen.addstr(row, col, dots)
            screen.addstr(row, col + len(dots),
                          node.artefact_digest or "None",
                          curses.color_pair(MyColorEnum.DIGEST.value))
            row += 1
            dots = '|  ' * indent + '|-- Digest S: '
            screen.addstr(row, col, dots)
            screen.addstr(row, col + len(dots),
                          # node.stored_digest or "None",
                          node.stored_digest or "None",
                          curses.color_pair(MyColorEnum.DIGEST.value))
            row += 1
            dots = '|  ' * indent + '|-- Digest C: '
            screen.addstr(row, col, dots)
            screen.addstr(row, col + len(dots),
                          # node.stored_digest or "None",
                          node.current_digest or "None",
                          curses.color_pair(MyColorEnum.DIGEST.value))
            row += 1

        for in_node in sorted(node.in_nodes, key=lambda node: node.__repr__()):
            row = print_tree(row, indent + 1, in_node)
        return row

    for node in sorted(g.root_nodes, key=lambda node: node.__repr__()):
        row = print_tree(row, 0, node)

    row += 1
    screen.addstr(row, 0, f"{len(g.nodes)} nodes ")
    row += 1
    # screen.addstr(row, 0, f"{len(g._leaf_artefacts())} leaves (source nodes)")
    # screen.move(first_row + cursor_tree_offset, 0)
    # screen.addstr(first_row + cursor_tree_offset, 0, '>',
    # curses.color_pair(MyColorEnum.CURSOR.value))

    screen.refresh()


def eval_command(screen, g):
    global current
    global hide_construction_command
    global cursor_tree_offset
    global cursor_tree_points_to
    global max_depth
    global hide_deps
    global hide_digest
    command = screen.getch()
    screen.addstr(0, 50, str(command))
    if command != -1:
        if command == ord('h'):
            help(screen)
            return

        if command == ord('c'):
            hide_construction_command = not hide_construction_command
        if command == ord('d'):
            hide_deps = not hide_deps
        if command == ord('g'):
            hide_digest = not hide_digest
        if command == ord('s'):
            scan(screen, g)
        if command == ord('b'):
            build(screen, g)
            scan(screen, g)
        if command == ord('-') and max_depth > 0:
            max_depth -= 1
        if command == ord('+') and max_depth < 10:
            max_depth += 1
        if command == curses.KEY_UP:
            cursor_tree_offset -= 1
        if command == curses.KEY_DOWN:
            cursor_tree_offset += 1
        if command == ord('q'):
            exit(0)

        print_tree(screen, g)


def _main(screen, g: lcpymake.world.World):
    global current
    global hide_construction_command
    global cursor_tree_offset
    global cursor_tree_points_to
    global max_depth
    global hide_deps
    global hide_digest

    init_colors(screen)
    # curses.curs_set(0)  # Hide the cursor
    screen.nodelay(True)  # Don't block I/O calls
    set_my_colors()

    while True:

        screen.addstr(1, 0, f"srcdir  : {g.srcdir}")
        screen.addstr(2, 0, f"sandbox : {g.sandbox}")

        info = f"max-depth:{max_depth}"
        if hide_construction_command:
            info = info + " c-"
        else:
            info = info + " c+"
        if hide_deps:
            info = info + " d-"
        else:
            info = info + " d+"
        if hide_digest:
            info = info + " g-"
        else:
            info = info + " g+"
        screen.addstr(0, 20, info)

        eval_command(screen, g)

        time.sleep(0.1)


def main(g):
    curses.wrapper(_main, g)


def show_colors():
    curses.wrapper(_show_colors)


if __name__ == "__main__":
    show_colors()
