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


def play(media, verbose=False):
    ic(media)
    media = Path(media)
    command = ["/usr/bin/mpv", "--no-audio-display", "--audio-display=no", "--image-display-duration=2", "--osd-on-seek=msg"]
    try:
        run_command("pidof X")
    except CalledProcessError:
        command.append("--vo=drm")
        command.append("--gpu-context=auto")

    command.append(media)
    if verbose:
        ic(command)
    run(command)


@click.command()
@click.argument("media", nargs=-1)
@click.option("--verbose", is_flag=True)
def cli(media, verbose):
    #play("/home/user/_youtube/sources/youtube/Thomas Winningham/th0ma5w__20110723__10 PRINT CHR$(205.5+RND(1));  - GOTO 10__m9joBLOZVEo.mp4")
    for m in media:
        play(m, verbose)
    pass


if __name__ == "__main__":
    cli()
