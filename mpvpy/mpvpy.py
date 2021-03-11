#!/usr/bin/env python3

# pylint: disable=C0111    # docstrings are always outdated and wrong
# pylint: disable=W0511    # todo is encouraged
# pylint: disable=C0301    # line too long
# pylint: disable=R0902    # too many instance attributes
# pylint: disable=C0302    # too many lines in module
# pylint: disable=C0103    # single letter var names, func name too descriptive
# pylint: disable=R0911    # too many return statements
# pylint: disable=R0912    # too many branches
# pylint: disable=R0915    # too many statements
# pylint: disable=R0913    # too many arguments
# pylint: disable=R1702    # too many nested blocks
# pylint: disable=R0914    # too many local variables
# pylint: disable=R0903    # too few public methods
# pylint: disable=E1101    # no member for base
# pylint: disable=W0201    # attribute defined outside __init__


import os
import sys
from pathlib import Path

import click
import mpv
from hashfilter.hashfilter import BannedHashError
from hashfilter.hashfilter import hashfilter
from icecream import ic
from jsonparser.jsonparser import jsonparser
from kcl.clipboardops import get_clipboard
from kcl.clipboardops import put_clipboard
from kcl.hashops import sha3_256_hash_file
from kcl.iterops import input_iterator
from kcl.printops import eprint
from kcl.terminalops import in_xorg

ic.configureOutput(includeContext=True)

BAN = False
PLAY_LATER = False
#QUIT = False

class BanChanError(ValueError):
    pass

class PlayChanLaterError(ValueError):
    pass

class BanClipboardError(ValueError):
    pass

class StopPlayingError(ValueError):
    pass

def logger(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message), file=sys.stderr)


def play(*,
         media,
         verbose: bool = False,
         debug: bool = False,
         video: bool = True,
         subtitles: bool = False,
         loop: bool = False,
         skip_ahead: float = None,
         ban_clipboard: bool = False,
         fullscreen: bool = False,):

    global QUIT
    QUIT = False
    global BAN
    BAN = False
    media = Path(media).absolute()
    ic(media.as_posix())
    #eprint(media.as_posix())

    if "/sha3_256/" in media.as_posix():
        ic('calculating sha3-256')
        file_hash = sha3_256_hash_file(media)
        ic(file_hash)
        try:
            hashfilter(sha3_256=file_hash,
                       group=None,
                       verbose=verbose,
                       debug=debug,)
        except BannedHashError as e:
            ic(e)
            ic('banned hash:', file_hash)
            return

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
    #ic(get_current_virtural_terminal())

    if not in_xorg():
        player.vo = "drm"
        player.gpu_context = "auto"

    if fullscreen:
        player.fullscreen = True

    if loop:
        player.loop_playlist = 'inf'

    if subtitles:
        player.sub = "yes"
    else:
        player.sub = "no"

    #if skip_ahead:
    #    player.start(skip_ahead)

    # https://github.com/jaseg/python-mpv/issues/122
    #player.on_key_press('ESC')(player.quit)
    #player.on_key_press('ENTER')(lambda: player.playlist_next(mode='force'))

    @player.on_key_press('Alt+i')
    def my_alt_i_binding():
        #ic('Alt+i works')
        media_ext = media.name.split(".")[-1]
        #ic(media_ext)
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
            #if os.getuid() == 0:
            #    os.system("su user -c \"/home/user/bin/spider-iri 1\" &")
            #else:
            #    os.system("/home/user/bin/spider-iri 1 &")
        else:
            if os.getuid() == 0:
                os.system("su user -c \"/usr/bin/iridb import {}\"".format(media.as_posix()))
            else:
                os.system("/usr/bin/iridb import {}".format(media.as_posix()))
        ic('done with Alt+i routine')

    @player.on_key_press('Meta+i')
    def my_meta_i_binding():
        ic('Meta+i works')

    @player.on_key_press('B')
    def my_s_binding():
        global BAN
        BAN = True
        ic('banning:', chan)
        #player.terminate()
        player.quit()
        #pillow_img = player.screenshot_raw()
        #pillow_img.save('screenshot.png')

    @player.on_key_press('L')
    def my_b_binding():
        global PLAY_LATER
        PLAY_LATER = True
        ic('PLAY_LATER:', chan)
        player.quit()

    #player.on_key_press('ENTER')(lambda: player.playlist_next(mode='force'))
    @player.on_key_press('ENTER')
    def my_enter_keybinding():
        ic()
        player.playlist_next(mode='force')

    # ESC must be pressed 2x if the focus is on the terminal due to mpv design:
    # https://github.com/jaseg/python-mpv/issues/122
    player.on_key_press('ESC')(player.quit)
    player.register_key_binding('INS', 'seek 5')

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
            if ban_clipboard:
                clipboard = get_clipboard(one_line=True)
                ic('raising BanClipboardError:', clipboard)
                raise BanClipboardError(clipboard)
            else:
                ic('raising BanChanError:', chan)
                raise BanChanError(chan)

        if PLAY_LATER:
            ic('raising PlayChanLaterError:', chan)
            raise PlayChanLaterError(chan)

        raise StopPlayingError
        #pass

    ic('calling player.terminate()')
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
@click.option("--printn", is_flag=True)
@click.option("--random", is_flag=True)
@click.option("--skip-ahead", type=int)
@click.option("--not-fullscreen", "--not-fs", is_flag=True)
@click.option("--verbose", is_flag=True)
@click.option("--debug", is_flag=True)
def cli(media,
        novideo,
        subtitles,
        loop,
        printn,
        random,
        skip_ahead,
        not_fullscreen,
        verbose: bool,
        debug: bool,):
    video = not novideo
    null = not printn
    fullscreen = not not_fullscreen
    if verbose:
        #ic(fullscreen)
        ic(skip_ahead)

    for m in input_iterator(strings=media,
                            random=random,
                            null=null,
                            verbose=verbose):
        play(media=m,
             video=video,
             subtitles=subtitles,
             loop=loop,
             verbose=verbose,
             debug=debug,
             fullscreen=fullscreen,
             skip_ahead=skip_ahead)

