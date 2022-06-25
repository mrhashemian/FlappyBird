import random
import sys
from itertools import cycle

import pygame
from pygame.constants import *

from config import config
from sprites import Bird, UpperPipe, LowerPipe


class FlappyBird:
    def __init__(self, game_title=config.game_title, screen_width=config.SCREENWIDTH,
                 screen_height=config.SCREENHEIGHT):
        self.game_title = game_title
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.sounds = None
        self.images = None
        self.screen = None
        self.fps_clock = None
        self.player_index_gen = cycle([0, 1, 2, 1])
        self.player_index = 0
        self.player_height = 0
        self.player_width = 0
        self.score = 0
        self.loop_iter = 0
        self.player_x = int(self.screen_width * 0.2)
        self.player_y = 0
        self.base_x = 0
        self.base_shift = 0
        self.bird_group = pygame.sprite.GroupSingle()
        self.pipe_group = pygame.sprite.Group()

    @staticmethod
    def simple_harmonic_motion(value, direction, boundary):
        if abs(value) == boundary:
            direction *= -1

        if direction == 1:
            value += 1
        else:
            value -= 1
        return {'value': value, 'direction': direction, 'boundary': boundary}

    def get_random_pipe(self):
        """returns a randomly generated pipe"""
        dt = self.fps_clock.tick(config.FPS) / 1000
        pipe_speed = -128 * dt

        gap_y = random.randrange(0, int(config.BASEY * 0.6 - config.PIPEGAPSIZE))
        gap_y += int(config.BASEY * 0.2)
        pipe_height = self.images['pipe'][0].get_height()
        pipe_x = self.screen_width + 10
        upper = UpperPipe(pipe_x, pipe_height - gap_y, pipe_speed, self.images)
        lower = LowerPipe(pipe_x, config.PIPEGAPSIZE + gap_y, pipe_speed, self.images)
        return [upper, lower]

    def show_score(self):
        """displays score in center of screen"""
        score_digits = [int(x) for x in list(str(self.score))]
        total_width = 0  # total width of all numbers to be printed

        for digit in score_digits:
            total_width += self.images['numbers'][digit].get_width()

        x_offset = (self.screen_width - total_width) / 2

        for digit in score_digits:
            self.screen.blit(self.images['numbers'][digit], (x_offset, self.screen_height * 0.1))
            x_offset += self.images['numbers'][digit].get_width()

    def welcome_animation(self):
        bird = Bird(self.player_x, self.player_y, self.images)
        self.bird_group.add(bird)

        message_x = int((self.screen_width - self.images['message'].get_width()) / 2)
        message_y = int(self.screen_height * 0.12)

        # player shm, simple harmonic motion, for up-down motion on welcome screen
        player_shm_values = {'value': 0, 'direction': 1, 'boundary': 12}

        while True:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN and (
                        event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                    self.sounds['wing'].play()
                    self.bird_group.remove(bird)
                    self.player_y = self.player_y + player_shm_values['value']
                    return

            # adjust player_y, player_index, base_x
            if (self.loop_iter + 1) % 5 == 0:
                self.player_index = next(self.player_index_gen)

            self.loop_iter = (self.loop_iter + 1) % 30  # base_x = -((-base_x + 4) % base_shift)
            self.base_x = (self.base_x - 4) % -self.base_shift
            player_shm_values = self.simple_harmonic_motion(**player_shm_values)

            # draw sprites
            self.screen.blit(self.images['background'], (0, 0))

            self.screen.blit(self.images['message'], (message_x, message_y))
            self.screen.blit(self.images['base'], (self.base_x, config.BASEY))

            self.bird_group.draw(self.screen)
            self.bird_group.update(self.images["player"][self.player_index],
                                   self.player_y + player_shm_values['value'])
            pygame.display.update()
            self.fps_clock.tick(config.FPS)

    def main_game(self):
        bird = Bird(self.player_x, self.player_y, self.images)
        self.bird_group.add(bird)

        pipe_list = []
        new_pipe = self.get_random_pipe()
        pipe_list.append(new_pipe)
        self.pipe_group.add(new_pipe[0])
        self.pipe_group.add(new_pipe[1])

        player_vel_y = -10
        player_flapped = False
        player_vel_rot = 3  # angular speed
        player_rot = 45

        while True:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN and (
                        event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                    if self.player_y > -0.4 * self.player_height:
                        player_vel_y = config.playerFlapAcc
                        player_flapped = True
                        self.sounds['wing'].play()

            # check for crash
            crash = pygame.sprite.spritecollide(self.bird_group.sprite, self.pipe_group, False,
                                                pygame.sprite.collide_mask)
            if crash or self.player_y + self.player_height >= config.BASEY - 1:
                return {
                    'ground_crash': False if crash else True,
                    'crash_pipe': crash[0] if crash else None,
                    'player_vel_y': player_vel_y,
                    'player_rot': player_rot
                }

            # check for score
            player_mid_pos = self.player_x + self.player_width / 2
            for pipe in pipe_list:
                pipe_mid_pos = pipe[0].x_cord() + self.images['pipe'][0].get_width() / 2
                if pipe_mid_pos <= player_mid_pos < pipe_mid_pos + 4:
                    self.score += 1
                    self.sounds['point'].play()

            # player_index base_x change
            if (self.loop_iter + 1) % 3 == 0:
                self.player_index = next(self.player_index_gen)

            self.loop_iter = (self.loop_iter + 1) % 30
            self.base_x = (self.base_x - 4) % -self.base_shift

            # rotate the player
            if player_rot > -90:
                player_rot -= player_vel_rot

            # player's movement
            if player_vel_y < config.playerMaxVelY and not player_flapped:
                player_vel_y += config.playerAccY
            if player_flapped:
                player_flapped = False

                # more rotation to cover the threshold (calculated in visible rotation)
                player_rot = 45

            self.player_y += min(player_vel_y, config.BASEY - self.player_y - self.player_height)

            if pipe_list[-1][0].x_cord() < self.screen_width - 130:
                new_pipe = self.get_random_pipe()
                pipe_list.append(new_pipe)
                self.pipe_group.add(new_pipe[0])
                self.pipe_group.add(new_pipe[1])

            # remove first pipe if its out of the screen
            if len(pipe_list) > 0 and pipe_list[0][0].x_cord() < -self.images['pipe'][0].get_width():
                pygame.sprite.Sprite.kill(pipe_list[0][0])
                pygame.sprite.Sprite.kill(pipe_list[0][1])
                pipe_list.pop(0)

            # draw sprites
            self.screen.blit(self.images['background'], (0, 0))

            visible_rot = min(player_rot, config.playerRotThr)

            player_surface = pygame.transform.rotate(self.images['player'][self.player_index], visible_rot)
            self.bird_group.draw(self.screen)
            self.bird_group.update(player_surface, self.player_y)
            self.pipe_group.update()
            self.pipe_group.draw(self.screen)
            self.show_score()
            self.screen.blit(self.images['base'], (self.base_x, config.BASEY))
            pygame.display.update()
            self.fps_clock.tick(config.FPS)

    def game_over(self, crash_info):
        """crashes the player down and shows game over image"""

        self.player_x = self.screen_width * 0.2

        player_vel_y = crash_info['player_vel_y']
        player_acc_y = 2
        player_rot = crash_info['player_rot']
        player_vel_rot = 7
        crash_pipe = crash_info['crash_pipe']

        # play hit and die sounds
        self.sounds['hit'].play()
        if not crash_info['ground_crash']:
            self.sounds['die'].play()

        while True:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN and (
                        event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                    if self.player_y + self.player_height >= config.BASEY - 1:
                        return

            # player y shift
            if self.player_y + self.player_height < config.BASEY - 1:
                self.player_y += min(player_vel_y, config.BASEY - self.player_y - self.player_height)

            # player velocity change
            if player_vel_y < 15:
                player_vel_y += player_acc_y

            # rotate only when it's a pipe crash
            if not crash_info['ground_crash']:
                if player_rot > -90:
                    player_rot -= player_vel_rot

            # draw sprites
            self.screen.blit(self.images['background'], (0, 0))
            if not crash_info['ground_crash']:
                self.screen.blit(crash_pipe.image, (crash_pipe.rect.x, crash_pipe.rect.y))

            self.screen.blit(self.images['base'], (self.base_x, config.BASEY))
            self.show_score()

            player_surface = pygame.transform.rotate(self.images['player'][1], player_rot)
            self.screen.blit(player_surface, (self.player_x, self.player_y))
            self.screen.blit(self.images['gameover'], (50, 180))

            self.fps_clock.tick(config.FPS)
            pygame.display.update()

    def validate(self):
        pass

    def pre_process(self):
        pygame.init()
        pygame.display.set_caption(self.game_title)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.fps_clock = pygame.time.Clock()

        rand_bg = random.randint(0, len(config.BACKGROUNDS_LIST) - 1)
        rand_player = random.randint(0, len(config.PLAYERS_LIST) - 1)
        pipe_index = random.randint(0, len(config.PIPES_LIST) - 1)

        self.sounds = {
            'die': pygame.mixer.Sound('assets/audio/die' + config.soundExt),
            'hit': pygame.mixer.Sound('assets/audio/hit' + config.soundExt),
            'point': pygame.mixer.Sound('assets/audio/point' + config.soundExt),
            'swoosh': pygame.mixer.Sound('assets/audio/swoosh' + config.soundExt),
            'wing': pygame.mixer.Sound('assets/audio/wing' + config.soundExt)
        }

        self.images = {
            'numbers': (
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
            ),
            'gameover': pygame.image.load('assets/sprites/gameover.png').convert_alpha(),
            'message': pygame.image.load('assets/sprites/message.png').convert_alpha(),
            'base': pygame.image.load('assets/sprites/base.png').convert_alpha(),
            'background': pygame.image.load(config.BACKGROUNDS_LIST[rand_bg]).convert(),
            'player': (
                pygame.image.load(config.PLAYERS_LIST[rand_player][0]).convert_alpha(),
                pygame.image.load(config.PLAYERS_LIST[rand_player][1]).convert_alpha(),
                pygame.image.load(config.PLAYERS_LIST[rand_player][2]).convert_alpha(),
            ),
            'pipe': (
                pygame.transform.rotate(pygame.image.load(config.PIPES_LIST[pipe_index]).convert_alpha(), 180),
                pygame.image.load(config.PIPES_LIST[pipe_index]).convert_alpha(),
            )
        }

        # amount by which base can maximum shift to left
        self.base_shift = self.images['base'].get_width() - self.images['background'].get_width()

        self.player_height = self.images['player'][0].get_height()
        self.player_width = self.images['player'][0].get_width()
        self.player_y = int((self.screen_height - self.player_height) / 2)

    def process(self):
        self.welcome_animation()
        crash_info = self.main_game()
        self.game_over(crash_info)

    def play(self):
        self.pre_process()
        return self.process()


if __name__ == "__main__":
    while True:
        FlappyBird().play()
