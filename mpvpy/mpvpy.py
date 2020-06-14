#!/usr/bin/env python3

import os
import click
from shutil import get_terminal_size
from kcl.commandops import run_command
from subprocess import CalledProcessError
from subprocess import run
from pathlib import Path
from icecream import ic
ic.configureOutput(includeContext=True)
ic.lineWrapWidth, _ = get_terminal_size((80, 20))


def play(media, verbose=False, video=True, subtitles=False, loop=False, skip_ahead=None):
    media = Path(media).absolute()
    ic(media.as_posix())
    mpv_command = ["/usr/bin/mpv", "--no-audio-display", "--audio-display=no", "--image-display-duration=2", "--osd-on-seek=msg"]
    if skip_ahead:
        mpv_command = mpv_command + ["--start=+" + str(skip_ahead)]

    if os.geteuid() == 0:
        command = ["schedtool", "-R", "-p", "20", "-n", "-12", "-e"] + mpv_command
    else:
        command = mpv_command

    if not subtitles:
        command.append('--sub=no')
    else:
        command.append('--sub=yes')

    if not video:
        command.append("--video=no")
    try:
        run_command("pidof X")
    except CalledProcessError:
        command.append("--vo=drm")
        command.append("--gpu-context=auto")

    if loop:
        command.append("--loop-file=inf")

    command.append(media)
    if verbose:
        ic(command)
    ic(command)
    run(command)


@click.command()
@click.argument("media", nargs=-1)
@click.option("--novideo", "--no-video", is_flag=True)
@click.option("--subtitles", is_flag=True)
@click.option("--loop", is_flag=True)
@click.option("--skip-ahead", type=int)
@click.option("--verbose", is_flag=True)
def cli(media, novideo, subtitles, loop, skip_ahead, verbose):
    video = not novideo
    if verbose:
        ic(skip_ahead)
    for m in media:
        if skip_ahead is None:
            if "/youtube/Seth Klein/" in m:
                skip_ahead = 4
        play(media=m, video=video, subtitles=subtitles, loop=loop, verbose=verbose, skip_ahead=skip_ahead)


if __name__ == "__main__":
    cli()
