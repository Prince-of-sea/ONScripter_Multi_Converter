#!/usr/bin/env python3
from pathlib import Path
from io import BytesIO
from PIL import Image
import concurrent.futures
import mozjpeg_lossless_optimization as mozj
import subprocess as sp
import imagequant as iq
import zopfli as zf
import tempfile
import shutil
import stat
import math
import os
import i18n

from requiredfile_locations import location, location_env
from conversion_music import convert_music
from utils import configure_progress_bar, subprocess_args


def getvidrenbanres(values: dict):
    # 連番変換時画像サイズ
    match values['vid_renbanres_radio']:
        case '100%(1/1)': renbanresper = 1
        case '75%(3/4)':  renbanresper = 0.750000
        case '66%(2/3)':  renbanresper = 0.666666
        case '50%(1/2)':  renbanresper = 0.500000
        case '33%(1/3)':  renbanresper = 0.333333
        case '25%(1/4)':  renbanresper = 0.250000
        case _: raise ValueError(i18n.t('ui.Video_sequential_image_size_not_found'))

    return renbanresper


def getvidframe(extractedpath: Path):

    # ffprobeのパス取得
    ffprobe_Path = location_env('ffprobe')

    # 動画情報を代入
    vid_frame_raw = sp.check_output([
        ffprobe_Path, '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', extractedpath,
    ], text=True, **subprocess_args(False))  # check_output時はFalse 忘れずに

    # fpsの上2桁を抽出(fpsが小数点の際たまに暴走して299700fpsとかになるので)& "/1" 削除
    vid_frame = (vid_frame_raw.replace('/1', ''))[:2]

    # (横幅/2の切り上げ)*2でfpsを偶数へ
    vid_frame = math.ceil(int(vid_frame)/2)*2  # だって奇数fpsの動画なんてまず無いし...

    return vid_frame


def getvidcodec(extractedpath: Path):

    # ffprobeのパス取得
    ffprobe_Path = location_env('ffprobe')

    # 動画情報を代入
    vid_codec = sp.check_output([
        ffprobe_Path, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name',
        '-of', 'default=noprint_wrappers=1:nokey=1', extractedpath,
    ], text=True, **subprocess_args(False))  # check_output時はFalse 忘れずに

    return vid_codec


def getvidaudio(extractedpath: Path):

    # ffprobeのパス取得
    ffprobe_Path = location_env('ffprobe')

    # 動画情報を代入
    vid_audio = sp.check_output([
        ffprobe_Path, '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=codec_type',
        '-of', 'default=noprint_wrappers=1:nokey=1', extractedpath,
    ], text=True, **subprocess_args(False))  # check_output時はFalse 忘れずに

    return bool('audio' in vid_audio)


def getvidplaytime(extractedpath: Path):

    # ffprobeのパス取得
    ffprobe_Path = location_env('ffprobe')

    # 動画情報を代入
    vid_playtime = sp.check_output([
        ffprobe_Path, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', extractedpath,
    ], text=True, **subprocess_args(False))  # check_output時はFalse 忘れずに

    vid_playtime = math.ceil(float(vid_playtime)*1000)

    return vid_playtime


def convert_video_mjpeg(values: dict, values_ex: dict, f_dict: dict):
    extractedpath = f_dict['extractedpath']
    convertedpath = f_dict['convertedpath']

    # smjpeg_encodeのパス取得
    smjpeg_encode_Path = location('smjpeg_encode')

    # ffmpegのパス取得
    ffmpeg_Path = location_env('ffmpeg')

    # fpsとコーデック取得
    vid_frame = getvidframe(extractedpath)
    vid_codec = getvidcodec(extractedpath)

    # 一時ディレクトリ作成
    with tempfile.TemporaryDirectory() as vidtemp_dir:
        vidtemp_dir = Path(vidtemp_dir)
        vidtemppath = Path(vidtemp_dir / extractedpath.name)

        # 展開前にPSPの再生可能形式(MPEG-1か2)へ
        if vid_codec == 'mpeg2video' or vid_codec == 'mpeg1video':  # 判定

            # そのまま再生できそうならコピー
            shutil.copy(extractedpath, vidtemppath)

            # 念の為読み取り専用を外す
            os.chmod(path=vidtemppath, mode=stat.S_IWRITE)

        else:
            # 拡張子偽装対策
            vidtemppath = vidtemppath.with_suffix('.mpg')

            # そのまま再生できなそうならエンコード
            sp.run([ffmpeg_Path, '-y',
                    '-i', extractedpath,
                    '-vcodec', 'mpeg2video',
                    '-qscale', '0',
                    str(vidtemppath),
                    ], **subprocess_args())

        # 縦横指定
        w = values_ex['output_resolution'][0]
        h = values_ex['output_resolution'][1]

        # 連番画像展開
        sp.run([ffmpeg_Path, '-y',
                '-i', vidtemppath,
                '-s', str(f'{w}:{h}'),
                '-r', str(vid_frame),
                '-qscale', str(values['vid_mjpegquality_bar']),
                str(vidtemp_dir) + '/%08d.jpg',  # 8桁連番
                ], **subprocess_args())

        # 音源抽出+16bitPCMへ変換
        if getvidaudio(extractedpath):
            sp.run([ffmpeg_Path, '-y',
                    '-i', vidtemppath,
                    '-f', 's16le',
                    '-vn',
                    '-ar', '44100',
                    '-ac', '2',
                    str(vidtemp_dir) + '/audiodump.pcm',
                    ], **subprocess_args())

        # -抽出ファイルをsmjpeg_encode.exeで結合-
        sp.run([smjpeg_encode_Path,
                '--video-fps', str(vid_frame),  # 小数点使用不可
                '--audio-rate', '44100',
                '--audio-bits', '16',
                '--audio-channels', '2',
                ],  cwd=vidtemp_dir, **subprocess_args())

        # 完成品を移動
        shutil.move((vidtemp_dir / r'output.mjpg'), convertedpath)

    return


def convert_video_renban(values: dict, values_ex: dict, f_dict: dict):
    extractedpath = f_dict['extractedpath']
    convertedpath = f_dict['convertedpath']
    hardware = values['hardware']
    vid_renbanaudset_radio = values['vid_renbanaudset_radio']
    aud_bgmch_radio = values['aud_bgmch_radio']
    aud_sech_radio = values['aud_sech_radio']

    # 連番の場合出力パスはディレクトリ扱いなのでとりあえず作成
    convertedpath.mkdir(exist_ok=True)

    # ffmpegのパス取得
    ffmpeg_Path = location_env('ffmpeg')

    # fps取得
    vid_frame = getvidframe(extractedpath)

    # 再生時間取得
    vid_playtime = getvidplaytime(extractedpath)

    # 再生時間受け渡し用ダミーファイル作成
    # 取得した再生時間をstr→listに変換し逆順でfor
    for keta, num in enumerate(reversed(list(str(vid_playtime))), 1):
        timedummypath = (convertedpath / f'keta{keta}_{num}')  # 保存先パス作成
        with open(timedummypath, 'wb') as s:
            s.write(b'\xff')  # ダミーファイルを書き込み - 内容空だと0kbでonsのfileexist無反応になるっぽい

    # 縦横指定
    if hardware == 'PSVITA':
        pw = math.ceil(540 / values_ex['output_resolution'][1]
                       * values_ex['output_resolution'][0])  # 基本960or725
        ph = 544

    else:
        pw = values_ex['output_resolution'][0]
        ph = values_ex['output_resolution'][1]

    w = math.ceil(pw * values_ex['renbanresper'])
    h = math.ceil(ph * values_ex['renbanresper'])

    # 連番画像展開
    sp.run([ffmpeg_Path, '-y',
            '-i', extractedpath,
            '-r', str(vid_frame),
            '-vf', f'scale={w}:{h},pad={pw}:{ph}:0:0:black',
            '-start_number', '0',
            # PNGで5桁連番 - jpgの場合も後で変換するので気にしなくて良い
            str(convertedpath) + '/_%05d.png',
            ], **subprocess_args())

    # 音源変換 - 動画を音声ファイルとして関数に投げさせる
    if getvidaudio(extractedpath):

        # ダミー辞書作成
        dummy_dict = {'extractedpath': extractedpath, 'nbz': False}

        # 音源をBGM/SEどっち扱いしてるか
        # bgm判定時
        if (vid_renbanaudset_radio == i18n.t('var.bgm_match')):
            if (aud_bgmch_radio == i18n.t('var.stereo')):
                dummy_dict['ch'] = '2'
            if (aud_bgmch_radio == i18n.t('var.mono')):
                dummy_dict['ch'] = '1'
            else:
                raise ValueError(
                    i18n.t('ui.Video_sequential_audio_bgm_channel_not_selected'))

            match values['aud_bgmfmt_radio']:
                case 'OGG':
                    dummy_dict['convertedpath'] = Path(
                        convertedpath / 'audio.ogg')
                    dummy_dict['format'] = 'OGG'
                    dummy_dict['kbps'] = values['aud_oggbgm_kbps']
                    dummy_dict['hz'] = values['aud_oggbgm_hz']

                case 'MP3':
                    dummy_dict['convertedpath'] = Path(
                        convertedpath / 'audio.mp3')
                    dummy_dict['format'] = 'MP3'
                    dummy_dict['cutoff'] = values['aud_mp3bgm_cutoff']
                    dummy_dict['kbps'] = values['aud_mp3bgm_kbps']
                    dummy_dict['hz'] = values['aud_mp3bgm_hz']

                case 'WAV':
                    dummy_dict['convertedpath'] = Path(
                        convertedpath / 'audio.wav')
                    dummy_dict['format'] = 'WAV'
                    dummy_dict['hz'] = values['aud_wavbgm_hz']

                    match values['aud_bgmcodec_radio']:
                        case 'pcm_s16le': dummy_dict['acodec'] = 'pcm_s16le'
                        case 'pcm_u8': dummy_dict['acodec'] = 'pcm_u8'
                        case _: raise ValueError(i18n.t('ui.Video_sequential_audio_bgm_wav_codec_not_found'))

                case _: raise ValueError(i18n.t('ui.Video_sequential_audio_bgm_format_not_found'))

        # se判定時
        elif (vid_renbanaudset_radio == i18n.t('var.se_voice_match')):
            if (aud_sech_radio == i18n.t('var.stereo')):
                dummy_dict['ch'] = '2'
            elif (aud_sech_radio == i18n.t('var.mono')):
                dummy_dict['ch'] = '1'
            else:
                raise ValueError(
                    i18n.t('ui.Video_sequential_audio_se_channel_not_selected'))

            match values['aud_sefmt_radio']:
                case 'OGG':
                    dummy_dict['convertedpath'] = Path(
                        convertedpath / 'audio.ogg')
                    dummy_dict['format'] = 'OGG'
                    dummy_dict['kbps'] = values['aud_oggse_kbps']
                    dummy_dict['hz'] = values['aud_oggse_hz']

                case 'MP3':
                    dummy_dict['convertedpath'] = Path(
                        convertedpath / 'audio.mp3')
                    dummy_dict['format'] = 'MP3'
                    dummy_dict['cutoff'] = values['aud_mp3se_cutoff']
                    dummy_dict['kbps'] = values['aud_mp3se_kbps']
                    dummy_dict['hz'] = values['aud_mp3se_hz']

                case 'WAV':
                    dummy_dict['convertedpath'] = Path(
                        convertedpath / 'audio.wav')
                    dummy_dict['format'] = 'WAV'
                    dummy_dict['hz'] = values['aud_wavse_hz']

                    match values['aud_secodec_radio']:
                        case 'pcm_s16le': dummy_dict['acodec'] = 'pcm_s16le'
                        case 'pcm_u8': dummy_dict['acodec'] = 'pcm_u8'
                        case _: raise ValueError(i18n.t('ui.Video_sequential_audio_se_wav_codec_not_found'))

                case _: raise ValueError(i18n.t('ui.Video_sequential_audio_se_format_not_found'))

        # 例外
        else:
            raise ValueError(
                i18n.t('ui.Video_sequential_audio_format_not_found'))

        # 音声抽出変換
        convert_music(dummy_dict)

        # ons再生簡略化のため拡張子を.musに統一
        shutil.move(dummy_dict['convertedpath'],
                    Path(convertedpath / 'audio.mus'))

    return


def convert_video_mp4(values: dict, values_ex: dict, f_dict: dict):
    hardware = values['hardware']
    extractedpath = f_dict['extractedpath']
    convertedpath = f_dict['convertedpath']

    # 出力用に拡張子mp4版用意
    convertedpath_mp4 = convertedpath.with_suffix('.mp4')

    # ffmpegのパス取得
    ffmpeg_Path = location_env('ffmpeg')

    # 縦横指定
    w = int(int(values_ex['output_resolution'][0])/2)*2
    h = int(int(values_ex['output_resolution'][1])/2)*2

    # 変換
    sp.run([ffmpeg_Path, '-y',
            '-i', extractedpath,
            '-s', f'{w}x{h}',
            '-vcodec', 'libx264',
            '-acodec', 'aac',
            '-ar', '44100',
            convertedpath_mp4,
            ], **subprocess_args())

    # PSVITA以外、なおかつ元々mp4ではないなら名前戻す
    if (hardware != 'PSVITA') and (convertedpath != convertedpath_mp4):
        shutil.move(convertedpath_mp4, convertedpath)

    return


def convert_video(values: dict, values_ex: dict, f_dict: dict):
    vid_movfmt_radio = values['vid_movfmt_radio']

    # ビデオの変換フォーマットによる分岐
    if (vid_movfmt_radio == i18n.t('var.numbered_images')):
        convert_video_renban(values, values_ex, f_dict)
    elif (vid_movfmt_radio == 'MJPEG'):
        convert_video_mjpeg(values, values_ex, f_dict)
    elif (vid_movfmt_radio == 'MP4'):
        convert_video_mp4(values, values_ex, f_dict)
    elif (vid_movfmt_radio == i18n.t('var.do_not_convert')):
        pass
    else:
        raise ValueError(i18n.t('ui.Video_conversion_format_not_selected'))


##########################################################################################
def convert_video_renban2_main(values: dict, imgpath: Path):
    # convert_image乗っ取りだと動作重い&画像縮小時に黒塗り部分の境界ボケるので仕方なくこっちに別で関数作成
    vid_renbanpngquantize_chk = bool(values['vid_renbanpngquantize_chk'])
    vid_renbanpngquantize_num = int(values['vid_renbanpngquantize_num'])
    vid_renbanjpgquality_bar = int(values['vid_renbanjpgquality_bar'])

    img = Image.open(imgpath)

    match values['vid_renbanfmt_radio']:
        case 'JPEG':
            convertedpath2 = imgpath.parent / \
                (str(imgpath.stem)[1:] + '.jpg')  # 名前最初の"_"切り取り

            # BytesIO/mozjpeg経由保存
            io_img = BytesIO()
            img.save(io_img, format='JPEG', quality=vid_renbanjpgquality_bar)
            io_img.seek(0)
            with open(convertedpath2, 'wb') as c:
                c.write(mozj.optimize(io_img.read()))

        case 'PNG':
            convertedpath2 = imgpath.parent / \
                (str(imgpath.stem)[1:] + '.png')  # 名前最初の"_"切り取り

            # imagequant/BytesIO/ZopfliPNG経由保存
            if vid_renbanpngquantize_chk:
                quant_img = iq.quantize_pil_image(
                    img, dithering_level=1.0, max_colors=vid_renbanpngquantize_num, min_quality=0, max_quality=100)
            else:
                quant_img = img
            io_img = BytesIO()
            quant_img.save(io_img, format='PNG')
            io_img.seek(0)
            with open(convertedpath2, 'wb') as c:
                c.write(zf.ZopfliPNG().optimize(io_img.read()))

        case _: raise ValueError(i18n.t('ui.Video_sequential_image_format_not_found'))

    # 変換終了後に元画像削除
    imgpath.unlink()

    return


def convert_video_renban2(values: dict, values_ex: dict, f_dict: dict, startbarnum: int, addbarnum: int,  useGUI: bool):
    num_workers = values_ex['num_workers']
    convertedpath = f_dict['convertedpath']

    # 並列ファイル変換
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []

        convertedpath_glob_png = convertedpath.glob(r'_*.png')
        convertedpath_glob_png_num = (len(list(convertedpath.glob(r'_*.png'))))

        for imgpath in convertedpath_glob_png:
            futures.append(executor.submit(
                convert_video_renban2_main, values, imgpath))

        for i, ft in enumerate(concurrent.futures.as_completed(futures)):
            # 進捗 0.35→0.95(繰り返しの合計)
            configure_progress_bar(
                startbarnum + (float(i / convertedpath_glob_png_num) * addbarnum), '', useGUI)

    return
