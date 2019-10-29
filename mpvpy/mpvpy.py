#!/usr/bin/env python3

import click
from shutil import get_terminal_size
from kcl.commandops import run_command
from subprocess import CalledProcessError
from subprocess import run
from pathlib import Path
from icecream import ic
ic.configureOutput(includeContext=True)
ic.lineWrapWidth, _ = get_terminal_size((80, 20))

#ic.disable()


def play(media):
    ic(media)
    media = Path(media)
    command = ["/usr/bin/mpv", "--no-audio-display", "--audio-display=no", "--image-display-duration=2", "--osd-on-seek=msg"]
    try:
        run_command("pidof X")
    except CalledProcessError:
        command.append("--vo=drm")
        command.append("--gpu-context=auto")

    command.append(media)
    ic(command)
    run(command)


@click.command()
@click.argument("media")
def cli(media):
    play("/home/user/_youtube/sources/youtube/Thomas Winningham/th0ma5w__20110723__10 PRINT CHR$(205.5+RND(1));  - GOTO 10__m9joBLOZVEo.mp4")
    pass


if __name__ == "__main__":
    cli()
