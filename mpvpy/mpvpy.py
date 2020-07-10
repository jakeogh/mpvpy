#!/usr/bin/env python3

import os
import sys
import mpv
from shutil import get_terminal_size
from kcl.commandops import run_command
from kcl.inputops import input_iterator
from subprocess import CalledProcessError
from subprocess import run
from pathlib import Path
from icecream import ic
import click

ic.configureOutput(includeContext=True)
ic.lineWrapWidth, _ = get_terminal_size((80, 20))

QUIT = False

def play(media,
         verbose=False,
         video=True,
         subtitles=False,
         loop=False,
         skip_ahead=None,
         fullscreen=False):

    global QUIT
    media = Path(media).absolute()
    ic(media.as_posix())

    media_parts = media.parts
    #ic(media_parts)
    if 'sources' in media_parts:
        sources_index = media_parts.index('sources')
        chan = media_parts[sources_index + 1:sources_index + 3]
        #ic(chan)
        chan = '/'.join(chan)
        #ic(chan)
        #import IPython; IPython.embed()


    player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True)

    if fullscreen:
        player.fullscreen = True

    if loop:
        player.loop_playlist = 'inf'

    @player.on_key_press('B')
    def my_s_binding():
        print(chan)
        #pillow_img = player.screenshot_raw()
        #pillow_img.save('screenshot.png')

    @player.on_key_press('ENTER')
    def my_enter_binding():
        player.playlist_next(mode='force')

    @player.on_key_press('ESC')
    def my_esc_binding():
        global QUIT
        QUIT = True
        player.terminate()
        #quit(1)
        #raise SystemExit

    player.play(media.as_posix())
    player.wait_for_playback()
    player.terminate()

    if QUIT:
        print("trying to quit")
        sys.exit(1)

    #mpv_command = ["/usr/bin/mpv", "--no-audio-display", "--audio-display=no", "--image-display-duration=2", "--osd-on-seek=msg"]
    #if skip_ahead:
    #    mpv_command = mpv_command + ["--start=+" + str(skip_ahead)]

    #if os.geteuid() == 0:
    #    command = ["schedtool", "-R", "-p", "20", "-n", "-12", "-e"] + mpv_command
    #else:
    #    command = mpv_command

    #if not subtitles:
    #    command.append('--sub=no')
    #else:
    #    command.append('--sub=yes')

    #if not video:
    #    command.append("--video=no")
    #try:
    #    run_command("pidof X")
    #except CalledProcessError:
    #    command.append("--vo=drm")
    #    command.append("--gpu-context=auto")

    #if loop:
    #    command.append("--loop-file=inf")

    #command.append(media)
    #if verbose:
    #    ic(command)

    #run(command)


@click.command()
@click.argument("media", nargs=-1)
@click.option("--novideo", "--no-video", is_flag=True)
@click.option("--subtitles", is_flag=True)
@click.option("--loop", is_flag=True)
@click.option("--null", is_flag=True)
@click.option("--skip-ahead", type=int)
@click.option("--fullscreen", is_flag=True)
@click.option("--verbose", is_flag=True)
def cli(media, novideo, subtitles, loop, null, skip_ahead, fullscreen, verbose):
    video = not novideo
    if verbose:
        ic(skip_ahead)

    for m in input_iterator(strings=media, null=null, verbose=verbose):
        play(media=m,
             video=video,
             subtitles=subtitles,
             loop=loop,
             verbose=verbose,
             skip_ahead=skip_ahead)

