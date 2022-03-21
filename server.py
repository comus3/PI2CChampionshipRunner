import asyncio
from inscription import inscription
from championship import championship
from ui import ui
from state import dumpState
import importlib
import argparse
from aiodebug import log_slow_callbacks
from logs import getLogger

log = getLogger('server')

async def main(gameName: str, port: int):
    #log_slow_callbacks.enable(0.5)
    log.info('Game Server For {}'.format(gameName.capitalize()))

    Game = importlib.import_module('games.{}.game'.format(gameName)).Game
    inscriptionTask = asyncio.create_task(inscription(port))
    championshipTask = asyncio.create_task(championship(Game))
    stateDumperTask = asyncio.create_task(dumpState())

    await ui()

    inscriptionTask.cancel()
    try:
        await inscriptionTask
    except asyncio.CancelledError:
        log.info('Inscription Task Stopped')
    
    championshipTask.cancel()
    try:
        await championshipTask
    except asyncio.CancelledError:
        log.info('Championship Task Stopped')
    
    stateDumperTask.cancel()
    try:
        await stateDumperTask
    except asyncio.CancelledError:
        log.info('State Dumper Task Stopped')
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('gameName', help='The name of the game')
    parser.add_argument('-p', '--port', help='The port the server use to listen for subscription', default=3000)
    args = parser.parse_args()

    asyncio.run(main(args.gameName, args.port))