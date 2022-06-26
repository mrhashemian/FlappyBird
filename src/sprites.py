import pygame


class Bird(pygame.sprite.Sprite):

    def __init__(self, x_loc, y_loc, images, idx=0, flapped=False):
        super(Bird, self).__init__()
        self.idx = idx
        self.flapped = flapped
        self.x_loc = x_loc
        self.y_loc = y_loc
        self.image = images["player"][0]
        self.rect = self.image.get_rect()
        self.rect.center = (x_loc, y_loc)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, player_surface, y):
        self.rect.y = y
        self.image = player_surface

    def bird_center(self):
        return self.rect.center


class UpperPipe(pygame.sprite.Sprite):

    def __init__(self, pipe_x, pipe_height, pipe_speed, images):
        super(UpperPipe, self).__init__()
        self.pipe_speed = pipe_speed
        self.pipe_height = pipe_height
        self.image = images['pipe'][0]
        self.rect = self.image.get_rect()
        self.rect.x = pipe_x
        self.rect.y = -pipe_height
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.x += self.pipe_speed

    def x_cord(self):
        return self.rect.x

    def y_cord(self):
        return self.rect.y + self.pipe_height


class LowerPipe(pygame.sprite.Sprite):

    def __init__(self, pipe_x, pipe_height, pipe_speed, images):
        super(LowerPipe, self).__init__()
        self.pipe_speed = pipe_speed
        self.pipe_height = pipe_height
        self.image = images['pipe'][1]
        self.rect = self.image.get_rect()
        self.rect.x = pipe_x
        self.rect.y = pipe_height
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.x += self.pipe_speed

    def x_cord(self):
        return self.rect.x

    def y_cord(self):
        return self.rect.y
