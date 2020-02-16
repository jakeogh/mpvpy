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


def play(media, verbose=False, video=True, subtitles=False):
    media = Path(media).absolute()
    ic(media.as_posix())
    command = ["/usr/bin/mpv", "--no-audio-display", "--audio-display=no", "--image-display-duration=2", "--osd-on-seek=msg"]
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

    command.append(media)
    if verbose:
        ic(command)
    run(command)


@click.command()
@click.argument("media", nargs=-1)
@click.option("--novideo", "--no-video", is_flag=True)
@click.option("--subtitles", is_flag=True)
@click.option("--verbose", is_flag=True)
def cli(media, novideo, subtitles, verbose):
    video = not novideo
    for m in media:
        play(media=m, video=video, subtitles=subtitles, verbose=verbose)


if __name__ == "__main__":
    cli()
