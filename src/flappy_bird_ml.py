import random
import sys
# from typing import Literal
from typing_extensions import Literal

import numpy as np
import pygame
from pygame.constants import *
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
from config import config
from flappy_bird import FlappyBird
from sprites import Bird


class FlappyBirdML(FlappyBird):
    def __init__(self, total_models=50, load_saved_pool=True, save_current_pool=False, train=True,
                 fitness_mode: Literal['tournament ', 'russian_roulette'] = 'russian_roulette'):
        super().__init__()
        self.total_models = total_models
        self.fitness = [0 for _ in range(self.total_models)]
        self.load_saved_pool = load_saved_pool
        self.save_current_pool = save_current_pool
        self.current_pool = []
        self.generation = 1
        self.train = train
        self.fitness_mode = fitness_mode
        self.bird_group = pygame.sprite.Group()

    def save_pool(self):
        for item, model in enumerate(self.current_pool):
            model.save_weights(f"Current_Model_Pool/model_new{item}.keras")
        print("current pool saved.")

    def model_fitness(self, fitness_mode, k=5):
        parent0 = np.random.randint(0, self.total_models)
        parent1 = np.random.randint(0, self.total_models)

        if fitness_mode == "russian_roulette":
            total_fitness = sum(self.fitness)
            for select in range(self.total_models):
                self.fitness[select] /= total_fitness
                if select > 0:
                    self.fitness[select] += self.fitness[select - 1]

            p_parent0 = random.uniform(0, 1)
            p_parent1 = random.uniform(0, 1)
            for ix in range(self.total_models):
                if self.fitness[ix] >= p_parent0:
                    parent0 = ix
                    break
            for ix in range(self.total_models):
                if self.fitness[ix] >= p_parent1:
                    parent1 = ix
                    break
            return parent0, parent1

        for ix in np.random.randint(0, self.total_models, k - 1):
            if self.fitness[ix] < self.fitness[parent0]:
                parent0 = ix
        for ix in np.random.randint(0, self.total_models, k - 1):
            if self.fitness[ix] < self.fitness[parent1]:
                parent1 = ix
        return parent0, parent1

    def model_crossover(self, model_1, model_2):
        weights0 = self.current_pool[model_1].get_weights()
        weights1 = self.current_pool[model_2].get_weights()

        n = len(weights1)
        start, end = random.randrange(n), random.randrange(n)
        if start > end:
            start, end = end, start
        child0 = weights0.copy()
        child1 = weights1.copy()
        for i in range(start, end + 1):
            child0[i] = weights1[i]
            child1[i] = weights0[i]

        return np.asarray([child0, child1])

    @staticmethod
    def model_mutate(weights, p_mutation):
        for xi in range(len(weights[0])):
            for yi in range(len(weights[0][xi])):
                if random.uniform(0, 1) > p_mutation:
                    change = random.uniform(-0.5, 0.5)
                    weights[0][xi][yi] += change
        for xi in range(len(weights[1])):
            for yi in range(len(weights[1][xi])):
                if random.uniform(0, 1) > p_mutation:
                    change = random.uniform(-0.5, 0.5)
                    weights[1][xi][yi] += change
        return weights

    def predict_jump_action(self, height, dist, pipe_height, model_num):
        # The height, dist and pipe_height must be between 0 to 1 (Scaled by SCREENHEIGHT)
        height = min(self.screen_height, height) / self.screen_height - 0.5
        dist = dist / 450 - 0.5  # Max pipe distance from player will be 450
        pipe_height = min(self.screen_height, pipe_height) / self.screen_height - 0.5
        neural_input = np.asarray([height, dist, pipe_height])
        neural_input = np.atleast_2d(neural_input)
        output_prob = self.current_pool[model_num].predict(neural_input, 1, verbose=0)[0]
        if output_prob[0] <= 0.5:
            # Perform the jump action
            return True
        return False

    @property
    def main_game(self):
        self.bird_group.empty()
        for player in range(self.total_models):
            y = random.randint(-60, 80)
            if not self.train:
                y = 0
            bird = Bird(self.player_x, self.player_y + y, self.images, player, False)
            self.bird_group.add(bird)

        pipe_list = []
        new_pipe = self.get_random_pipe(self.screen_width + 200)
        pipe_list.append(new_pipe)
        self.pipe_group.empty()
        self.pipe_group.add(new_pipe[0])
        self.pipe_group.add(new_pipe[1])

        next_pipe_x = pipe_list[0][1].pipe_center()[0]
        next_pipe_hole_y = (pipe_list[0][1].pipe_center()[1] + pipe_list[0][0].pipe_center()[1]) / 2

        players_vel_y = [-9 for _ in range(self.total_models)]

        while True:
            alive_players = len(self.bird_group.sprites())

            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()

            for bird in self.bird_group.sprites():
                if bird.y_loc < 0:
                    self.bird_group.remove(bird)

            if alive_players == 0:
                return {
                    'ground_crash': True,
                    'crash_pipe': None,
                    'player_vel_y': players_vel_y[0],
                }

            for bird in self.bird_group.sprites():
                self.fitness[bird.idx] += 1

            next_pipe_x += -4
            for bird in self.bird_group.sprites():
                # if random.choice([True, False, False, False, False, False, False, False, False, False]):
                if self.predict_jump_action(bird.y_loc, next_pipe_x, next_pipe_hole_y, bird.idx):
                    if bird.y_loc > -2 * self.player_height:
                        players_vel_y[bird.idx] = config.playerFlapAcc
                        bird.flapped = True

            # check for crash
            pygame.sprite.groupcollide(self.bird_group, self.pipe_group, True, False, pygame.sprite.collide_mask)

            # check for score
            for bird in self.bird_group.sprites():
                for pipe_idx, pipe in enumerate(pipe_list):
                    pipe_mid_pos = pipe[0].x_cord() + self.images['pipe'][0].get_width()
                    if pipe_mid_pos <= self.player_x < pipe_mid_pos + 4:
                        next_pipe_x = pipe_list[pipe_idx + 1][1].pipe_center()[0]
                        next_pipe_hole_y = (pipe_list[pipe_idx + 1][1].pipe_center()[1] +
                                            pipe_list[pipe_idx + 1][0].pipe_center()[1]) / 2

                        self.score += 1
                        self.fitness[bird.idx] += 25
            if (self.loop_iter + 1) % 3 == 0:
                self.player_index = next(self.player_index_gen)

            self.loop_iter = (self.loop_iter + 1) % 30
            self.base_x = (self.base_x - 4) % -self.base_shift

            # player's movement
            for bird in self.bird_group.sprites():
                if players_vel_y[bird.idx] < config.playerMaxVelY and not bird.flapped:
                    players_vel_y[bird.idx] += config.playerAccY
                if bird.flapped:
                    bird.flapped = False

                bird.y_loc += min(players_vel_y[bird.idx], config.BASEY - bird.y_loc - self.player_height)

                # check for ground crash
                if bird.y_loc + self.player_height >= config.BASEY - 1:
                    self.bird_group.remove(bird)

            # add new pipe
            if pipe_list[-1][0].x_cord() < self.screen_width - 130:
                new_pipe = self.get_random_pipe()
                pipe_list.append(new_pipe)
                self.pipe_group.add(new_pipe[0])
                self.pipe_group.add(new_pipe[1])

            # remove first pipe if its out of the screen
            if len(pipe_list) > 0 and pipe_list[0][0].x_cord() < -self.images['pipe'][0].get_width():
                self.pipe_group.remove(pipe_list[0][0])
                self.pipe_group.remove(pipe_list[0][1])
                pipe_list.pop(0)

            # draw screen
            self.screen.blit(self.images['background'], (0, 0))
            player_surface = self.images['player'][self.player_index]
            for bird in self.bird_group.sprites():
                bird.update(player_surface, bird.y_loc)
            self.bird_group.draw(self.screen)

            self.pipe_group.update()
            self.pipe_group.draw(self.screen)
            self.show_score()
            pygame.draw.circle(self.screen, (255, 0, 0), (next_pipe_x - 3, next_pipe_hole_y), 6)  # E
            self.screen.blit(self.images['base'], (self.base_x, config.BASEY))
            pygame.display.update()
            self.fps_clock.tick(config.FPS)

    def game_over(self, crash_info):
        new_population = []

        for select in range(int(self.total_models / 2)):
            parent0, parent1 = self.model_fitness(k=10, fitness_mode=self.fitness_mode)
            new_weights = self.model_crossover(parent0, parent1)
            new_weights = self.model_mutate(new_weights, p_mutation=0.75)
            new_population.append(new_weights[0])
            new_population.append(new_weights[1])

        for select in range(len(new_population)):
            self.fitness[select] = -100
            self.current_pool[select].set_weights(new_population[select])
        if self.save_current_pool and self.train:
            self.save_pool()
        self.generation = self.generation + 1
        self.score = 0

    def process(self):
        while True:
            crash_info = self.main_game
            self.game_over(crash_info)

    def play(self):
        # Initialize all models
        for i in range(self.total_models):
            model = Sequential()
            model.add(Dense(units=7, input_dim=3, activation='sigmoid'))
            model.add(Dense(units=1, activation="sigmoid"))

            sgd = SGD(learning_rate=0.01, decay=1e-6, momentum=0.9, nesterov=True)
            model.compile(loss="mse", optimizer=sgd, metrics=["accuracy"])
            self.current_pool.append(model)
            self.fitness.append(-100)

            if self.train and self.load_saved_pool:
                self.current_pool[i].load_weights(f"Current_Model_Pool/model_new{i}.keras")
            elif self.load_saved_pool:
                self.current_pool[i].load_weights(
                    f"TrainedModels/Individual_Best_Trained_Models/model_trained{i + 1}.keras")

        # for i in range(self.total_models):
        #     print(self.current_pool[i].get_weights())

        self.pre_process()
        self.process()


if __name__ == "__main__":
    FlappyBirdML(total_models=50, train=True, save_current_pool=True, load_saved_pool=False,
                 fitness_mode='russian_roulette').play()
    # FlappyBirdML(total_models=2, train=False).play()
