import pygame
import operator


class ScoreBoard(object):
    def __init__(self):
        self.scoreboard = {}

    def sort_score(self):
        return dict(sorted(self.scoreboard.items(), key=operator.itemgetter(1), reverse=True))

    def update_score(self, name, score):
        try:
            if self.scoreboard[name] > score:
                return False
        except KeyError:
            pass
        self.scoreboard.update({name:score})
        self.sort_score()
        return True

    def draw_score(self, surface, x, y):
        count = 1
        for key in self.scoreboard:
            text = "%i %s %s" %(count, key, self.scoreboard[key])
            draw_text(surface, text, x, y + 12 * (count - 1))
            count += 1

pygame.init()
display = pygame.display.set_mode((640, 480))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 12)

score_board = ScoreBoard()
score_board.update_score("Hosung", 100)
score_board.update_score("Dalton", 103)
score_board.update_score("Dalton", 173)
score_board.update_score("Dalton", 3)


def draw_text(surface, text, x, y, color=(0, 0, 0)):
    _text = font.render(text, False, color)
    surface.blit(_text, (x, y))

while True:
    display.fill((255, 255, 255))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
    score_board.draw_score(display, 10, 10)
    pygame.display.flip()
    clock.tick(60)