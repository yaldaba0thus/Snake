from random import randint
from enum import Enum
from time import monotonic

import pygame


COLOR_FIELD = (72, 145, 116)  # #489174
COLOR_FONT = (255, 255, 255)  # #FFFFFF
COLOR_BODY = (14, 87, 58)  # #0E573A
COLOR_HEAD = (0, 58, 35)  # #003A23

COLOR_BORDER = (5, 28, 56)  # #051C38
COLOR_APPLE = (20, 49, 83)  # #143153


class GameStatus(Enum):
    RUNNING = 0
    WON = 1
    LOST = 2


class Duration(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class Apple:
    def __init__(self, rows, cols, snake) -> None:
        while True:
            self.x = randint(0, cols - 1)
            self.y = randint(0, rows - 1)
            if not self._check_collision_snake(snake):
                break

    def _check_collision_snake(self, snake):
        current = snake.head
        while current is not None:
            if current.x == self.x and current.y == self.y:
                return True
            current = current.next
        return False

    def render(self, screen, cell_width, cell_height) -> None:
        pygame.draw.rect(
            screen,
            COLOR_APPLE,
            pygame.rect.Rect(
                self.x * cell_width + 2,
                self.y * cell_height + 2,
                cell_width - 2,
                cell_height - 2,
            )
        )


class BodyCell:
    def __init__(self, x, y, next = None) -> None:
        self.x = x
        self.y = y
        self.next = next

    def update(self, x, y) -> None:
        self.x = x
        self.y = y

    def render(self, screen, cell_width, cell_height, is_head) -> None:
        if is_head:
            pygame.draw.rect(
                screen,
                COLOR_HEAD,
                pygame.rect.Rect(
                    self.x * cell_width + 2,
                    self.y * cell_height + 2,
                    cell_width - 2,
                    cell_height - 2,
                )
            )
        else:
            pygame.draw.rect(
                screen,
                COLOR_BODY,
                pygame.rect.Rect(
                    self.x * cell_width + 2,
                    self.y * cell_height + 2,
                    cell_width - 2,
                    cell_height - 2,
                )
            )


class Snake:
    def __init__(self, rows, cols) -> None:
        self.length = 1
        self.head = BodyCell(
            randint(0, cols - 1),
            randint(0, rows - 1),
        )
        self.pretail = self.head
        self.tail = self.head
        self.dx = 0
        self.dy = 0
        self.duration = None
        self.speed = 0.2

    def check_collision_itself(self) -> bool:
        current = self.head.next
        while current is not None:
            if current.x == self.head.x and current.y == self.head.y:
                return True
            current = current.next
        return False

    def check_collision_apple(self, apple: Apple) -> bool:
        if self.head.x == apple.x and self.head.y == apple.y:
            if self.length == 1:
                self.tail.next = BodyCell(self.head.x + self.dx, self.head.y + self.dy)
            else:
                dx = self.tail.x - self.pretail.x
                dy = self.tail.y - self.pretail.y
                self.tail.next = BodyCell(self.tail.x + dx, self.tail.y + dy)
                self.pretail = self.tail
            self.tail = self.tail.next
            self.length += 1
            self.speed -= 0.001
            return True
        return False
    
    def check_collision_borders(self, rows, cols) -> bool:
        if self.head.x < 0 or self.head.x >= cols or self.head.y < 0 or self.head.y >= rows:
            return True
        return False

    def move(self, duration) -> None:
        match duration:
            case Duration.UP:
                if self.duration == Duration.DOWN:
                    return
                self.dy = -1
                self.dx = 0
            case Duration.DOWN:
                if self.duration == Duration.UP:
                    return
                self.dy = 1
                self.dx = 0
            case Duration.RIGHT:
                if self.duration == Duration.LEFT:
                    return
                self.dx = 1
                self.dy = 0
            case Duration.LEFT:
                if self.duration == Duration.RIGHT:
                    return
                self.dx = -1
                self.dy = 0
        self.duration = duration

    def update(self) -> None:
        current = self.head
        current_x, current_y = current.x, current.y
        current.update(current.x + self.dx, current.y + self.dy)
        current = current.next
        while current is not None:
            tmp_x, tmp_y = current.x, current.y
            current.update(current_x, current_y)
            current_x, current_y = tmp_x, tmp_y
            current = current.next

    def render(self, screen, cell_width, cell_height) -> None:
        self.head.render(screen, cell_width, cell_height, True)
        current = self.head.next
        while current is not None:
            current.render(screen, cell_width, cell_height, False)
            current = current.next


class Field:
    def __init__(
        self,
        rows: int,
        cols: int,
    ) -> None:
        self.rows = rows
        self.cols = cols

    def render(self, screen: pygame.Surface, cell_width, cell_height) -> None:
        for row in range(self.rows):
            pygame.draw.line(
                screen,
                COLOR_BORDER,
                (0, row * cell_height),
                (screen.get_width(), row * cell_height),
                2,
            )

        for col in range(self.cols):
            pygame.draw.line(
                screen,
                COLOR_BORDER,
                (col * cell_width, 0),
                (col * cell_width, screen.get_height()),
                2,
            )


class Game:
    def __init__(self) -> None:
        pygame.init()

        pygame.display.set_caption("Snake")
        self.width = 1200
        self.height = 1200
        self.rows = 10
        self.cols = 10
        self.cell_width = self.width / self.cols
        self.cell_height = self.height / self.rows
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        self.delta_time = 0
        self.running = True
        self.status = GameStatus.RUNNING

        self.field = Field(self.rows, self.cols)
        self.snake = Snake(self.rows, self.cols)
        self.apple = Apple(self.rows, self.cols, self.snake)
        self.last_update_time = monotonic()
        self.was_key_down = False

    def _handle_event(self) -> None:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.running = False
                case pygame.KEYDOWN:
                    if not self.was_key_down:
                        match event.key:
                            case pygame.K_a:
                                self.snake.move(Duration.LEFT)
                            case pygame.K_d:
                                self.snake.move(Duration.RIGHT)
                            case pygame.K_w:
                                self.snake.move(Duration.UP)
                            case pygame.K_s:
                                self.snake.move(Duration.DOWN)
                    self.was_key_down = True

    def _check_collision(self) -> None:
        if self.snake.check_collision_apple(self.apple):
            self.apple = Apple(self.rows, self.cols, self.snake)
        if (
            self.snake.check_collision_borders(self.rows, self.cols) or
            self.snake.check_collision_itself()
        ):
            self.status = GameStatus.LOST

    def _update(self) -> None:
        current_time = monotonic()
        if (
            current_time - self.last_update_time >= self.snake.speed and
            self.status == GameStatus.RUNNING
        ):
            self.snake.update()
            self.last_update_time = current_time
            self.was_key_down = False

    def _render(self) -> None:
        self.screen.fill(COLOR_FIELD)
        self.field.render(self.screen, self.cell_width, self.cell_height)
        self.apple.render(self.screen, self.cell_width, self.cell_height)
        self.snake.render(self.screen, self.cell_width, self.cell_height)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self._handle_event()
            self._update()
            self._check_collision()
            self._render()
            self.delta_time = self.clock.tick(60) / 1000

        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
