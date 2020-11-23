import time
import curses


from lcpymake import model


class Colormap:
    bg = 44


def init_colors(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(0, -1, curses.COLOR_BLUE)
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    # stdscr.bkgd(' ', curses.color_pair(44) | curses.A_BOLD)
    stdscr.bkgd(' ', curses.color_pair(Colormap.bg) | curses.A_BOLD | curses.A_REVERSE)


def _show_colors(stdscr):
    init_colors(stdscr)
    curses.curs_set(0)    # Hide the cursor
    try:
        for i in range(0, 255):
            row = i // 10
            col = i - row * 10
            stdscr.addstr(row + 5, 0, f"{row*10:003}")
            stdscr.addstr(row + 5, col * 4 + 10, f"{i:003}", curses.color_pair(i))
    except Exception:
        # End of screen reached
        pass
    stdscr.getch()


count = 0


def splash(screen):
    global count
    chars = "|/-\\|/-\\"
    c = chars[count % len(chars)]
    screen.addstr(0, 0, c)
    count += 1


def _main(screen, g: model.World):

    init_colors(screen)
    curses.curs_set(0)    # Hide the cursor
    screen.nodelay(True)  # Don't block I/O calls

    directions = {
        curses.KEY_UP: (-1, 0),
        curses.KEY_DOWN: (1, 0),
        curses.KEY_LEFT: (0, -1),
        curses.KEY_RIGHT: (0, 1),
    }

    direction = directions[curses.KEY_RIGHT]
    snake = [(0, i) for i in reversed(range(20))]

    while True:
        screen.erase()
        splash(screen)

        screen.addstr(1, 0, str(g.srcdir))
        screen.addstr(2, 0, str(g.sandbox), curses.color_pair(27))

        # Draw the snake
        screen.addstr(*snake[0], '@')
        for segment in snake[1:]:
            screen.addstr(*segment, '*')

        # Move the snake
        snake.pop()
        snake.insert(0, tuple(map(sum, zip(snake[0], direction))))

        # Change direction on arrow keystroke
        direction = directions.get(screen.getch(), direction)

        screen.refresh()
        time.sleep(0.1)


def main(g):
    curses.wrapper(_main, g)


def show_colors():
    curses.wrapper(_show_colors)


if __name__ == "__main__":
    show_colors()
