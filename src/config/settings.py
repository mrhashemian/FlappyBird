import sys
from pydantic import BaseSettings


class Settings(BaseSettings):
    debug = True
    game_title = "Flappy Bird"
    log_level = "INFO"

    FPS = 30
    SCREENWIDTH = 288
    SCREENHEIGHT = 512
    PIPEGAPSIZE = 100  # gap between upper and lower part of pipe
    BASEY = SCREENHEIGHT * 0.79

    # list of all possible players
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
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'

    playerMaxVelY = 10  # max vel along Y, max descend speed
    playerMinVelY = -8  # min vel along Y, max ascend speed - no use
    playerAccY = 1  # players downward acceleration
    playerRotThr = 20  # rotation threshold
    playerFlapAcc = -9  # players speed on flapping


config = Settings()
