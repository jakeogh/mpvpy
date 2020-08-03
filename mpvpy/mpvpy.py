#!/usr/bin/env python3

import os
import sys
import mpv
from shutil import get_terminal_size
from kcl.commandops import run_command
from kcl.inputops import input_iterator
from kcl.clipboardops import put_clipboard
from kcl.printops import eprint
from jsonparser.jsonparser import jsonparser
from subprocess import CalledProcessError
from subprocess import run
from pathlib import Path
from icecream import ic
import click

ic.configureOutput(includeContext=True)
ic.lineWrapWidth, _ = get_terminal_size((80, 20))

#QUIT = False
BAN = False

class BanChanError(ValueError):
    pass

class StopPlayingError(ValueError):
    pass

def logger(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message), file=sys.stderr)


def play(media,
         verbose=False,
         video=True,
         subtitles=False,
         loop=False,
         skip_ahead=None,
         fullscreen=False):

    global QUIT
    QUIT = False
    global BAN
    BAN = False
    media = Path(media).absolute()
    ic(media.as_posix())
    eprint(media.as_posix())

    media_parts = media.parts
    if 'sources' in media_parts:
        sources_index = media_parts.index('sources')
        chan = media_parts[sources_index + 1:sources_index + 3]
        #ic(chan)
        chan = '/'.join(chan)
        #import IPython; IPython.embed()

    if video:
        video = 'auto'

    player = mpv.MPV(log_handler=logger,
                     input_default_bindings=True,
                     terminal=True,
                     input_terminal=True,
                     input_vo_keyboard=True,
                     #script_opts='osc-layout=bottombar,osc-seekbarstyle=bar,osc-deadzonesize=0,osc-minmousemove=3',
                     #script_opts='osc-layout=bottombar',
                     osd_bar=False,
                     scripts='/home/user/.config/mpv/osc_seek.lua',
                     #osc=True,
                     video=video)

    # self.m = mpv.MPV(vo='x11')
    try:
        run_command("pidof X")
    except CalledProcessError:
        #vo = drm
        player.vo("drm")
        player.gpu_context("auto")
        #command.append("--vo=drm")
        #command.append("--gpu-context=auto")

    if fullscreen:
        player.fullscreen = True

    if loop:
        player.loop_playlist = 'inf'

    #if skip_ahead:
    #    player.start(skip_ahead)

    # https://github.com/jaseg/python-mpv/issues/122
    #player.on_key_press('ESC')(player.quit)
    #player.on_key_press('ENTER')(lambda: player.playlist_next(mode='force'))

    @player.on_key_press('Ctrl+i')
    def my_ctrl_i_binding():
        media_ext = media.name.split(".")[-1]
        #if media_ext:
        media_json_file = media.as_posix().replace("." + media_ext, ".info.json")
        ic(media_json_file)
        try:
            url = jsonparser(path=media_json_file, key="webpage_url")
            ic(url)
        except UnicodeDecodeError:
            #ic(e)  # nope, will print the binary that was not json
            url = None

        if url:
            put_clipboard(url)
            os.system("su user -c \"/home/user/bin/spider-iri 1\"")
        else:
            os.system("su user -c \"/usr/bin/iridb import {}\"".format(media.as_posix()))


    @player.on_key_press('B')
    def my_s_binding():
        global BAN
        BAN = True
        print("banning:", chan)
        player.terminate()
        #pillow_img = player.screenshot_raw()
        #pillow_img.save('screenshot.png')

    player.on_key_press('ENTER')(lambda: player.playlist_next(mode='force'))

    # ESC must be pressed 2x if the focus is on the terminal due to mpv design:
    # https://github.com/jaseg/python-mpv/issues/122
    player.on_key_press('ESC')(player.quit)

    #@player.on_key_press('ESC')
    #def my_esc_binding():
    #    #player.quit()
    #    global QUIT
    #    QUIT = True
    #    player.terminate()

    try:
        player.play(media.as_posix())
        # https://github.com/jaseg/python-mpv/issues/79
        if skip_ahead:
            player.wait_for_property('seekable')
            player.seek(skip_ahead, reference='absolute', precision='exact')
        player.wait_for_playback()
    except mpv.ShutdownError:
        eprint("\nmpv.ShutdownError\n")
        player.terminate()
        if BAN:
            raise BanChanError(chan)
            return
        raise StopPlayingError
        #pass

    player.terminate()

    #if player.vo_configured:  # True when window is closed https://github.com/jaseg/python-mpv/issues/122
    #    print("sys.exit(0)", file=sys.stderr)
    #    sys.exit(0)

    #if QUIT:
    #    player.terminate()
    #    sys.exit(0)


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
@click.option("--fullscreen", "--fs", is_flag=True)
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


