from itertools import cycle
import random
import sys
import pygame
from pygame.locals import *

FPS = 30
SCREENWIDTH = 288
SCREENHEIGHT = 512
PIPEGAPSIZE = 120  # gap between upper and lower part of pipe
BASEY = SCREENHEIGHT * 0.89
# image, sound and hitmask  dicts
IMAGES, SOUNDS, HITMASKS = {}, {}, {}

# list of all possible players (tuple of 3 positions of flap)
PLAYERS_LIST = (
    # red bird
    (
        'assets/sprites/redbird-upflap.png',
        'assets/sprites/redbird-midflap.png',
        'assets/sprites/redbird-downflap.png',
    ),
    # blue bird
    (
        'assets/sprites/bluebird-upflap.png',
        'assets/sprites/bluebird-midflap.png',
        'assets/sprites/bluebird-downflap.png',
    ),
    # yellow bird
    (
        'assets/sprites/yellowbird-upflap.png',
        'assets/sprites/yellowbird-midflap.png',
        'assets/sprites/yellowbird-downflap.png',
    ),
)

# list of backgrounds
BACKGROUNDS_LIST = (
    'assets/sprites/background-day.png',
    'assets/sprites/background-night.png',
)

# list of pipes
PIPES_LIST = (
    'assets/sprites/pipe-green.png',
    'assets/sprites/pipe-red.png',
)


def main():
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    pygame.display.set_caption('Flappy Bird')

    # numbers sprites for score display
    IMAGES['numbers'] = (
        pygame.image.load('assets/sprites/0.png').convert_alpha(),
        pygame.image.load('assets/sprites/1.png').convert_alpha(),
        pygame.image.load('assets/sprites/2.png').convert_alpha(),
        pygame.image.load('assets/sprites/3.png').convert_alpha(),
        pygame.image.load('assets/sprites/4.png').convert_alpha(),
        pygame.image.load('assets/sprites/5.png').convert_alpha(),
        pygame.image.load('assets/sprites/6.png').convert_alpha(),
        pygame.image.load('assets/sprites/7.png').convert_alpha(),
        pygame.image.load('assets/sprites/8.png').convert_alpha(),
        pygame.image.load('assets/sprites/9.png').convert_alpha()
    )

    # game over sprite
    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    # message sprite for welcome screen
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    # base (ground) sprite
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()

    # sounds
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'

    SOUNDS['die'] = pygame.mixer.Sound('assets/audio/die' + soundExt)
    SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit' + soundExt)
    SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point' + soundExt)
    SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
    SOUNDS['wing'] = pygame.mixer.Sound('assets/audio/wing' + soundExt)

    while True:
        # sprites = pygame.sprite.Group()

        # select random background sprites
        randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
        IMAGES['background'] = pygame.image.load(BACKGROUNDS_LIST[randBg]).convert()

        # select random player sprites
        randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
        IMAGES['player'] = (
            pygame.image.load(PLAYERS_LIST[randPlayer][0]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][1]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][2]).convert_alpha(),
        )

        # select random pipe sprites
        pipeindex = random.randint(0, len(PIPES_LIST) - 1)
        IMAGES['pipe'] = (
            pygame.transform.rotate(
                pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), 180),
            pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(),
        )

        # hitmask for pipes

        movementInfo = showWelcomeAnimation()
        crashInfo = mainGame(movementInfo)
        showGameOverScreen(crashInfo)


class Bird(pygame.sprite.Sprite):
    """ Will contain the bird attributes.
        Args:
        x_loc (int): X - coordinate of the center of the bird sprite
        y_loc (int): Y - coordinate of the center of the bird sprite
        velocity (int): Velocity of the bird sprite. """

    def __init__(self, x_loc, y_loc, velocity):
        super(Bird, self).__init__()
        self.check = 0
        self.velocity = velocity
        self.x_loc = x_loc
        self.y_loc = y_loc
        self.image = IMAGES["player"][0]
        # self.image.set_colorkey(WHITE)
        # self.image = pygame.transform.scale(self.image, (40, 40))
        self.rect = self.image.get_rect()
        self.rect.center = (x_loc, y_loc)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, player_surface, y):
        self.rect.y = y
        # print("aa", a)
        self.image = player_surface
        # self.velocity = self.velocity + 1

    # def jump(self):
    #     self.velocity = -10

    # def boundary_collison(self):
    #     if self.rect.bottom + 100 >= display_height or self.rect.top <= 0:
    #         return True

    def bird_center(self):
        return self.rect.center

    # def vel(self):
    #     return velocity


class UpperPipe(pygame.sprite.Sprite):
    """ Will contain the upper pipe's attributes.
        Args:
        pipe_x (int): X - coordinate of the starting of the pipe
        pipe_height (int): Height of the upper pipe
        pipe_speed (int): Pipe speed with which they pipe's will move horizontally. """

    def __init__(self, pipe_x, pipe_height, pipe_speed):
        super(UpperPipe, self).__init__()
        self.pipe_speed = pipe_speed
        self.pipe_height = pipe_height
        self.image = IMAGES['pipe'][0]
        # self.image.fill(GREEN)
        # self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = SCREENWIDTH
        self.rect.y = -pipe_height
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        # print("update")
        self.rect.x += self.pipe_speed

    def x_cord(self):
        # print(self.rect.x)
        return self.rect.x

    def y_cord(self):
        return self.rect.y + self.pipe_height


class LowerPipe(pygame.sprite.Sprite):
    """ Will contain the lower pipe's attributes.
        Args:
        pipe_x (int): X - coordinate of the starting of the pipe
        pipe_height (int): Height of the lower pipe
        pipe_speed (int): Pipe speed with which they pipe's will move horizontally. """

    def __init__(self, pipe_x, pipe_height, pipe_speed):
        super(LowerPipe, self).__init__()
        self.pipe_speed = pipe_speed
        self.pipe_height = pipe_height
        self.image = IMAGES['pipe'][1]
        self.rect = self.image.get_rect()
        self.rect.x = SCREENWIDTH  # pipe_x
        self.rect.y = pipe_height
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.x += self.pipe_speed

    def x_cord(self):
        return self.rect.x

    def y_cord(self):
        return self.rect.y


def showWelcomeAnimation():
    """Shows welcome screen animation of flappy bird"""
    # index of player to blit on screen
    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    # iterator used to change playerIndex after every 5th iteration
    loopIter = 0

    playerx = int(SCREENWIDTH * 0.2)
    playery = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)
    bird_group = pygame.sprite.Group()
    bird = Bird(playerx, playery, 1)
    bird_group.add(bird)

    messagex = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    messagey = int(SCREENHEIGHT * 0.12)

    basex = 0
    # amount by which base can maximum shift to left
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # player shm for up-down motion on welcome screen
    playerShmVals = {'val': 0, 'dir': 1}

    while True:
        print(bird)
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                # make first flap sound and return values for mainGame
                # print("h")
                SOUNDS['wing'].play()
                # pygame.sprite.Sprite.kill(bird)
                bird_group.remove(bird)
                print(bird)
                return {
                    'playery': playery + playerShmVals['val'],
                    'basex': basex,
                    'playerIndexGen': playerIndexGen,
                }

        # adjust playery, playerIndex, basex
        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)

        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)
        playerShm(playerShmVals)

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0, 0))


        SCREEN.blit(IMAGES['message'], (messagex, messagey))
        SCREEN.blit(IMAGES['base'], (basex, BASEY))

        bird_group.draw(SCREEN)
        bird_group.update(IMAGES["player"][playerIndex], playery + playerShmVals['val'])
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def mainGame(movementInfo):
    pipe_group = pygame.sprite.Group()
    score = playerIndex = loopIter = 0
    playerIndexGen = movementInfo['playerIndexGen']
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo['playery']

    bird_group = pygame.sprite.GroupSingle()
    bird = Bird(playerx, playery, 1)
    bird_group.add(bird)

    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()


    pipe_list = []
    newPipe = getRandomPipe()
    pipe_list.append(newPipe)
    pipe_group.add(newPipe[0])
    pipe_group.add(newPipe[1])


    dt = FPSCLOCK.tick(FPS) / 1000
    pipeVelX = -128 * dt

    # player velocity, max velocity, downward acceleration, acceleration on flap
    playerVelY = -9  # player's velocity along Y, default same as playerFlapped
    playerMaxVelY = 10  # max vel along Y, max descend speed
    playerMinVelY = -8  # min vel along Y, max ascend speed
    playerAccY = 1  # players downward acceleration
    playerRot = 45  # player's rotation
    playerVelRot = 3  # angular speed
    playerRotThr = 20  # rotation threshold
    playerFlapAcc = -9  # players speed on flapping
    playerFlapped = False  # True when player flaps

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                if playery > -0.4 * IMAGES['player'][0].get_height():
                    # print(playery, IMAGES['player'][0].get_height())
                    playerVelY = playerFlapAcc
                    playerFlapped = True
                    SOUNDS['wing'].play()

        # check for crash here
        crash = pygame.sprite.spritecollide(bird_group.sprite, pipe_group, False, pygame.sprite.collide_mask)

        if crash:
            return {
                'y': playery,
                'groundCrash': False,
                'basex': basex,
                'crash_pipe': crash[0],
                'score': score,
                'playerVelY': playerVelY,
                'playerRot': playerRot
            }
        if playery + IMAGES['player'][0].get_height() >= BASEY - 1:
            return {
                'y': playery,
                'groundCrash': True,
                'basex': basex,
                'crash_pipe': None,
                'score': score,
                'playerVelY': playerVelY,
                'playerRot': playerRot
            }

        # check for score
        playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
        # print(playerMidPos)
        for pipe in pipe_list:
            # print(, "s")
            pipeMidPos = pipe[0].x_cord() + IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                SOUNDS['point'].play()

        # playerIndex basex change
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 100) % baseShift)

        # rotate the player
        if playerRot > -90:
            playerRot -= playerVelRot

        # player's movement
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False

            # more rotation to cover the threshold (calculated in visible rotation)
            playerRot = 45

        playerHeight = IMAGES['player'][playerIndex].get_height()
        playery += min(playerVelY, BASEY - playery - playerHeight)

        if pipe_list[-1][0].x_cord() < SCREENWIDTH - 130:

            newPipe = getRandomPipe()
            pipe_list.append(newPipe)
            pipe_group.add(newPipe[0])
            pipe_group.add(newPipe[1])


        # remove first pipe if its out of the screen
        if len(pipe_list) > 0 and pipe_list[0][0].x_cord() < -IMAGES['pipe'][0].get_width():
            pygame.sprite.Sprite.kill(pipe_list[0][0])
            pygame.sprite.Sprite.kill(pipe_list[0][1])
            pipe_list.pop(0)

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0, 0))


        visibleRot = playerRotThr
        if playerRot <= playerRotThr:
            visibleRot = playerRot

        playerSurface = pygame.transform.rotate(IMAGES['player'][playerIndex], visibleRot)
        bird_group.draw(SCREEN)
        bird_group.update(playerSurface, playery)
        pipe_group.update()
        pipe_group.draw(SCREEN)
        showScore(score)
        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def showGameOverScreen(crashInfo):
    """crashes the player down and shows gameover image"""
    score = crashInfo['score']
    playerx = SCREENWIDTH * 0.2
    playery = crashInfo['y']
    playerHeight = IMAGES['player'][0].get_height()
    playerVelY = crashInfo['playerVelY']
    playerAccY = 2
    playerRot = crashInfo['playerRot']
    playerVelRot = 7

    basex = crashInfo['basex']

    crash_pipe = crashInfo['crash_pipe']

    # play hit and die sounds
    SOUNDS['hit'].play()
    if not crashInfo['groundCrash']:
        SOUNDS['die'].play()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                if playery + playerHeight >= BASEY - 1:
                    return

        # player y shift
        if playery + playerHeight < BASEY - 1:
            playery += min(playerVelY, BASEY - playery - playerHeight)

        # player velocity change
        if playerVelY < 15:
            playerVelY += playerAccY

        # rotate only when it's a pipe crash
        if not crashInfo['groundCrash']:
            if playerRot > -90:
                playerRot -= playerVelRot

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0, 0))
        if not crashInfo['groundCrash']:
            SCREEN.blit(crash_pipe.image, (crash_pipe.rect.x, crash_pipe.rect.y))

        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        showScore(score)

        playerSurface = pygame.transform.rotate(IMAGES['player'][1], playerRot)
        SCREEN.blit(playerSurface, (playerx, playery))
        SCREEN.blit(IMAGES['gameover'], (50, 180))

        FPSCLOCK.tick(FPS)
        pygame.display.update()


def playerShm(playerShm):
    """oscillates the value of playerShm['val'] between 8 and -8"""
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1

    if playerShm['dir'] == 1:
        playerShm['val'] += 1
    else:
        playerShm['val'] -= 1


def getRandomPipe():
    """returns a randomly generated pipe"""
    dt = FPSCLOCK.tick(FPS) / 1000
    pipe_speed = -128 * dt

    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeHeight = IMAGES['pipe'][0].get_height()
    pipeX = SCREENWIDTH + 10
    print(pipeHeight, gapY, "ss")
    upper = UpperPipe(pipeX, pipeHeight - gapY, pipe_speed)
    lower = LowerPipe(pipeX, PIPEGAPSIZE + gapY, pipe_speed)
    return [upper, lower]


def showScore(score):
    """displays score in center of screen"""
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0  # total width of all numbers to be printed

    for digit in scoreDigits:
        totalWidth += IMAGES['numbers'][digit].get_width()

    Xoffset = (SCREENWIDTH - totalWidth) / 2

    for digit in scoreDigits:
        SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.1))
        Xoffset += IMAGES['numbers'][digit].get_width()


if __name__ == '__main__':
    main()
