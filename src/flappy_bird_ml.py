import random
import sys
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
    def __init__(self, ):
        super().__init__()
        self.total_models = 50
        self.fitness = [0 for _ in range(self.total_models)]
        self.load_saved_pool = False
        self.save_current_pool = True
        self.current_pool = []
        self.next_pipe_x = -1
        self.next_pipe_hole_y = -1
        self.generation = 1
        self.bird_group = pygame.sprite.Group()

    def save_pool(self):
        for item, model in enumerate(self.current_pool):
            model.save_weights(f"Current_Model_Pool/model_new{item}.keras")
        print("current pool saved.")

    def model_crossover(self, model_1, model_2):
        weights1 = self.current_pool[model_1].get_weights()
        weights2 = self.current_pool[model_2].get_weights()
        # weights1[0], weights1[1] = weights2[1], weights2[0]
        weightsnew1 = weights1
        weightsnew2 = weights2
        weightsnew1[0] = weights2[0]
        weightsnew2[0] = weights1[0]
        # new_weight_1 = weights1[0] + weights2[1]
        # new_weight_2 = weights2[0] + weights1[1]
        # print(type(weightsnew1), len(weightsnew1))
        return np.asarray([weightsnew1, weightsnew2])

    def model_mutate(self, weights):
        for xi in range(len(weights)):
            for yi in range(len(weights[xi])):
                if random.uniform(0, 1) > 0.85:
                    change = random.uniform(-0.5, 0.5)
                    weights[xi][yi] += change
        return weights

    # def mutate(self, master):
    #     mutation = np.random.normal(scale=1)
    #     return master + mutation

    def predict_jump_action(self, height, dist, pipe_height, model_num):
        # The height, dist and pipe_height must be between 0 to 1 (Scaled by SCREENHEIGHT)
        height = min(self.screen_height, height) / self.screen_height - 0.5
        dist = dist / 450 - 0.5  # Max pipe distance from player will be 450
        pipe_height = min(self.screen_height, pipe_height) / self.screen_height - 0.5
        neural_input = np.asarray([height, dist, pipe_height])
        neural_input = np.atleast_2d(neural_input)
        output_prob = self.current_pool[model_num].predict(neural_input, 1)[0]
        if output_prob[0] <= 0.5:
            # Perform the jump action
            return True
        return False

    @property
    def main_game(self):
        self.bird_group.empty()
        for player in range(self.total_models):
            bird = Bird(self.player_x, self.player_y, self.images, player, False)
            self.bird_group.add(bird)

        pipe_list = []
        new_pipe = self.get_random_pipe(self.screen_width + 120)
        pipe_list.append(new_pipe)
        self.pipe_group.empty()
        self.pipe_group.add(new_pipe[0])
        self.pipe_group.add(new_pipe[1])

        self.next_pipe_x = pipe_list[0][0].x_cord()
        self.next_pipe_hole_y = (pipe_list[0][0].y_cord() + (
                pipe_list[0][1].y_cord() + self.images['pipe'][0].get_height())) / 2

        # dot = pygame.Surface((5, 5))
        # dot.fill((255, 0, 0))
        # self.screen.blit(dot, (self.next_pipe_x, self.next_pipe_hole_y))

        players_vel_y = [-9 for _ in range(self.total_models)]
        player_vel_rot = 3  # angular speed
        player_rot = 45

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
                    'player_rot': player_rot
                }

            for bird in self.bird_group.sprites():
                self.fitness[bird.idx] += 1

            self.next_pipe_x += -4

            for bird in self.bird_group.sprites():
                if random.choice([True, False, False, False, False, False, False, False, False, False]):
                    # if self.predict_jump_action(bird.y_loc, self.next_pipe_x, self.next_pipe_hole_y, bird.idx):
                    if bird.y_loc > -2 * self.player_height:
                        players_vel_y[bird.idx] = config.playerFlapAcc
                        bird.flapped = True

            # check for crash
            pygame.sprite.groupcollide(self.bird_group, self.pipe_group, True, False, pygame.sprite.collide_mask)

            # check for score
            for bird in self.bird_group.sprites():
                for pipe in pipe_list:
                    pipe_mid_pos = pipe[0].x_cord() + self.images['pipe'][0].get_width()
                    if pipe_mid_pos <= self.player_x < pipe_mid_pos + 4:
                        self.score += 1
                        self.fitness[bird.idx] += 25

            if (self.loop_iter + 1) % 3 == 0:
                self.player_index = next(self.player_index_gen)

            self.loop_iter = (self.loop_iter + 1) % 30
            self.base_x = (self.base_x - 4) % -self.base_shift

            # rotate the player
            if player_rot > -90:
                player_rot -= player_vel_rot

            # player's movement
            for bird in self.bird_group.sprites():
                if players_vel_y[bird.idx] < config.playerMaxVelY and not bird.flapped:
                    players_vel_y[bird.idx] += config.playerAccY
                if bird.flapped:
                    bird.flapped = False
                    player_rot = 45
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

            # draw sprites
            self.screen.blit(self.images['background'], (0, 0))
            player_surface = self.images['player'][self.player_index]
            self.bird_group.draw(self.screen)
            for bird in self.bird_group.sprites():
                bird.update(player_surface, bird.y_loc)

            self.pipe_group.update()
            self.pipe_group.draw(self.screen)
            self.show_score()
            self.screen.blit(self.images['base'], (self.base_x, config.BASEY))
            pygame.display.update()
            self.fps_clock.tick(config.FPS)

    def game_over(self, crash_info):
        new_weights = []
        total_fitness = sum(self.fitness)
        for select in range(self.total_models):
            self.fitness[select] /= total_fitness
            if select > 0:
                self.fitness[select] += self.fitness[select - 1]
        for select in range(int(self.total_models / 2)):
            parent1 = random.uniform(0, 1)
            parent2 = random.uniform(0, 1)
            idx1 = -1
            idx2 = -1
            for idxx in range(self.total_models):
                if self.fitness[idxx] >= parent1:
                    idx1 = idxx
                    break
            for idxx in range(self.total_models):
                if self.fitness[idxx] >= parent2:
                    idx2 = idxx
                    break
            # print(idx1, idx2)
            new_weights1 = self.model_crossover(idx1, idx2)
            # print(type(new_weights1), len(new_weights1))
            updated_weights1 = self.model_mutate(new_weights1[0])
            updated_weights2 = self.model_mutate(new_weights1[1])
            new_weights.append(updated_weights1)
            new_weights.append(updated_weights2)
            # new_weights.append(new_weights1[0])
            # new_weights.append(new_weights1[1])
        for select in range(len(new_weights)):
            self.fitness[select] = -100
            self.current_pool[select].set_weights(new_weights[select])
        if self.save_current_pool:
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

            # model.add(Activation("sigmoid"))
            model.add(Dense(units=1, activation="sigmoid"))
            # model.add(Activation("sigmoid"))

            sgd = SGD(learning_rate=0.01, decay=1e-6, momentum=0.9, nesterov=True)
            model.compile(loss="mse", optimizer=sgd, metrics=["accuracy"])
            self.current_pool.append(model)
            self.fitness.append(-100)

        if self.load_saved_pool:
            for i in range(self.total_models):
                self.current_pool[i].load_weights("Current_Model_Pool/model_new" + str(i) + ".keras")

        # for i in range(self.total_models):
        #     print(self.current_pool[i].get_weights())

        self.pre_process()
        self.process()


if __name__ == "__main__":
    FlappyBirdML().play()
