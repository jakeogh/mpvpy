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
from math import inf
from pathlib import Path
from typing import Optional
from typing import Union

import click
import mpv
from asserttool import ic
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tv
from clipboardtool import get_clipboard
from clipboardtool import put_clipboard
from eprint import eprint
#from mptool import unmp
from hashfilter.hashfilter import BannedHashError
from hashfilter.hashfilter import hashfilter
from hashtool import sha3_256_hash_file
from jsonparser.jsonparser import jsonparser
from mptool import unmp
from terminaltool import in_xorg

BAN = False
PLAY_LATER = False
QUIT = False


class BanChanError(ValueError):
    pass

class PlayChanLaterError(ValueError):
    pass

class BanClipboardError(ValueError):
    pass

class StopPlayingError(ValueError):
    pass

class StopPlayingAfterError(ValueError):
    pass

def logger(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message), file=sys.stderr)


def extract_chan(path: Path,
                 verbose: Union[bool, int, float],
                 ) -> str:
    path_parts = path.parts
    if 'sources' in path_parts:
        sources_index = path_parts.index('sources')
        chan = path_parts[sources_index + 1:sources_index + 3]
        #ic(chan)
        chan = '/'.join(chan)
        return chan
    raise ValueError('/sources/ not in path: {}'.format(path.as_posix()))


def check_for_banned_hash(*,
                          media: Path,
                          verbose: Union[bool, int, float],
                          ):

    if "/sha3_256/" in media.as_posix():
        ic('calculating sha3-256')
        file_hash = sha3_256_hash_file(media, verbose=verbose,)
        ic(file_hash)
        try:
            hashfilter(sha3_256=file_hash,
                       group=None,
                       verbose=verbose,
                       )
        except BannedHashError as e:
            ic(e)
            ic('banned hash:', file_hash)
            return True
    return False


def play(*,
         media,
         verbose: Union[bool, int, float],
         novideo: bool = False,
         noaudio: bool = False,
         subtitles: bool = False,
         loop: bool = False,
         skip_ahead: Optional[float] = None,
         ban_clipboard: bool = False,
         fullscreen: bool = False,
         ):

    global QUIT
    QUIT = False
    global BAN
    BAN = False
    media = Path(media).absolute()
    ic(media.as_posix())

    if check_for_banned_hash(media=media,
                             verbose=verbose,
                             ):
        return

    #assert 'sources' in media.parts
    try:
        chan = extract_chan(path=media, verbose=verbose,)
    except ValueError:
        chan = None

    video = not novideo
    audio = not noaudio  # todo
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

    if not in_xorg(verbose=verbose):
        player.vo = "drm"
        player.gpu_context = "auto"
    else:
        player.vo = 'gpu'
        player.hwdec = 'vaapi'

    if fullscreen:
        player.fullscreen = True

    if loop:
        #player.loop_playlist = 'inf'
        player.loop_file = 'inf'

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
        try:
            media_json_file = media.as_posix().replace("." + media_ext, ".info.json")
            ic(media_json_file)
            url = jsonparser(path=media_json_file, key="webpage_url")
            ic(url)
        except (UnicodeDecodeError, PermissionError):
            #ic(e)  # nope, will print the binary that was not json
            url = None

        if url:
            put_clipboard(url, verbose=verbose,)
            if os.getuid() == 0:
                os.system("su user -c \"/home/user/bin/spider-iri 1\" &")
            else:
                os.system("/home/user/bin/spider-iri 1 &")
        else:
            if os.getuid() == 0:
                os.system("su user -c \"/usr/bin/iridb import '{}'\"".format(media.as_posix()))
            else:
                os.system("/usr/bin/iridb import {}".format(media.as_posix()))
        ic('done with Alt+i routine')

    @player.on_key_press('Meta+i')
    def my_meta_i_binding():
        ic('Meta+i works')

    @player.on_key_press('D')
    def my_D_binding():
        ic('D works')
        os.system('mv -vi ' + '"' + media.as_posix() + '"' + ' /delme/')

    @player.on_key_press('B')
    def my_B_binding():
        global BAN
        BAN = True
        ic('banning:', chan)
        #player.terminate()
        player.quit()
        #pillow_img = player.screenshot_raw()
        #pillow_img.save('screenshot.png')

    @player.on_key_press('L')
    def my_L_binding():
        global PLAY_LATER
        PLAY_LATER = True
        ic('PLAY_LATER:', chan)
        player.quit()

    @player.on_key_press('Meta+L')
    def my_meta_L_binding():
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
                clipboard = get_clipboard(one_line=True, verbose=verbose,)
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
@click.option("--noaudio", "--no-audio", is_flag=True)
@click.option("--subtitles", is_flag=True)
@click.option("--loop", is_flag=True)
@click.option("--random", is_flag=True)
@click.option("--skip-ahead", type=int)
@click.option("--not-fullscreen", "--not-fs", is_flag=True)
@click_add_options(click_global_options)
def cli(media: Optional[tuple[str]],
        novideo: bool,
        noaudio: bool,
        subtitles: bool,
        loop: bool,
        random: bool,
        skip_ahead: int,
        not_fullscreen,
        verbose: Union[bool, int, float],
        verbose_inf: bool,
        ):

    #video = not novideo
    fullscreen = not not_fullscreen
    if verbose:
        #ic(fullscreen)
        ic(media, skip_ahead)

    skip_set = set()
    if media:
        iterator = media
    else:
        iterator = unmp(verbose=verbose, valid_types=[bytes,])

    for index, m in enumerate(iterator):
    #for index, m in enumerate_input(iterator=media,
    #                                random=random,
    #                                verbose=verbose,
    #                                ):
        path = Path(os.fsdecode(m))
        if verbose:
            ic(path)
        try:
            chan = extract_chan(path=path,
                                verbose=verbose,
                                )
            if chan in skip_set:
                continue
        except ValueError:
            pass

        try:
            play(media=path,
                 novideo=novideo,
                 noaudio=noaudio,
                 subtitles=subtitles,
                 loop=loop,
                 verbose=verbose,
                 fullscreen=fullscreen,
                 skip_ahead=skip_ahead,)

        except PlayChanLaterError as e:
            chan = e.args[0]
            skip_set.add(chan)
