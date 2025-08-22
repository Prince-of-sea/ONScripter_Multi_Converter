#!/usr/bin/env python3
from pathlib import Path
import math
import i18n
import re

from utils import openread0x84bitxor, lower_AtoZ


def onsscript_decode(values: dict):
    input_dir = Path(values['input_dir'])
    charset = values['charset']

    # 優先順位は00.txt > 0.txt > nscript.dat
    ztxt_path = Path(input_dir / '0.txt')
    zztxt_path = Path(input_dir / '00.txt')
    nsdat_path = Path(input_dir / 'nscript.dat')

    text = ''

    if zztxt_path.exists():
        for i in range(0, 100):
            zzrange_path = Path(input_dir / (str(i).zfill(2) + '.txt'))
            if zzrange_path.exists():
                with open(zzrange_path, 'r', encoding=charset, errors='ignore') as zzrangetext:
                    text += zzrangetext.read()
                    text += f'\n\n;##\n;{zzrange_path.name} end\n;##\n\n'

    elif ztxt_path.exists():
        for i in range(0, 10):
            zrange_path = Path(input_dir / (str(i) + '.txt'))
            if zrange_path.exists():
                with open(zrange_path, 'r', encoding=charset, errors='ignore') as zrangetext:
                    text += zrangetext.read()
                    text += f'\n\n;##\n;{zrange_path.name} end\n;##\n\n'

    elif nsdat_path.exists():
        text += openread0x84bitxor(nsdat_path, charset)

    else:
        raise FileNotFoundError(i18n.t('ui.No_script_file_found'))

    return text


def onsscript_check_resolution(values: dict, values_ex: dict, ztxtscript: str, override_resolution: list):
    hardware = values['hardware']
    aspect_43only = values_ex['aspect_4:3only']
    charset = values['charset']

    # 解像度表記抽出
    oldnsc_mode = (
        r';[Mm][Oo][Dd][Ee](320|400|800)')  # ONS解像度旧表記
    newnsc_mode = (
        r';\$([A-z][0-9]+)*[Ss]([0-9]+),([0-9]+)([A-z][0-9]+)*')  # ONS解像度新表記
    newnsc_search = re.search(newnsc_mode, ztxtscript)
    oldnsc_search = re.search(oldnsc_mode, ztxtscript)

    # 解像度表記を元に解像度を取得して変数に格納
    if oldnsc_search:
        script_resolution = (int(oldnsc_search.group(1)),
                             int(int(oldnsc_search.group(1)) / 4 * 3))

    elif newnsc_search:
        script_resolution = (int(newnsc_search.group(2)),
                             int(newnsc_search.group(3)))

    else:
        script_resolution = (640, 480)

    # PSPは解像度新表記が読めないので、強制的に旧表記に変換(ついでに非対応解像度時エラー)
    if (hardware == 'PSP') and (newnsc_search):
        script_w = script_resolution[0]
        script_h = script_resolution[1]

        # スクリプト横解像度が800や640に近いときに代替横解像度作成
        if (script_w != 800) and (script_w > 790) and (script_w < 810):
            alternative_w = 800
        elif (script_w != 640) and (script_w > 630) and (script_w < 650):
            alternative_w = 640
        else:
            alternative_w = False

        # 代替横解像度作成時
        if alternative_w:

            # 代替縦 = 代替横 / 入力横 * 入力縦
            alternative_h = round(alternative_w / script_w * script_h)

            # 出力縦 = 270固定(272だと左右若干見切れるor微妙に縦長くなるのでNG)
            output_h = 270

            # 出力横 = 出力縦 * 代替横 / 代替縦
            output_w = round(output_h * alternative_w / alternative_h)

            # 出力横を2の倍数(切り捨て)に
            output_w = int(math.floor(output_w / 2) * 2)

            # 出力横が480超えない(=画面比率が16:9より横長かったりしない)なら
            if (output_w <= 480):
                override_resolution = (output_w, output_h)

    if (aspect_43only) and (newnsc_search):

        # グローバル数取得
        newnsc_mode_gvar = (
            r';\$([A-z][0-9]+(,([0-9]+))?)*[Gg]([0-9]+)([A-z][0-9]+(,([0-9]+))?)*')
        newnsc_mode_gvar_search = re.search(newnsc_mode_gvar, ztxtscript)
        g_value_num = newnsc_mode_gvar_search.group(
            4) if newnsc_mode_gvar_search else '200'

        # チェック&変換
        if (hardware == 'PSP') and (override_resolution) and (charset == 'cp932'):  # 日本語版PSPのみ
            if (alternative_w == 800):
                ztxtscript = re.sub(
                    newnsc_mode, f';mode800,value{g_value_num}', ztxtscript, 1)# ほぼ800変換時
            elif (alternative_w == 640):
                ztxtscript = re.sub(
                    newnsc_mode, f';value{g_value_num}', ztxtscript, 1)# ほぼ640変換時
            else:
                ztxtscript = re.sub(
                    newnsc_mode, f';value{g_value_num}', ztxtscript, 1)# 解像度無視時

        elif (script_resolution[0] in [320, 400, 640, 800]) and (script_resolution[1] == script_resolution[0] / 4 * 3):
            if (script_resolution[0] == 640):
                ztxtscript = re.sub(
                    newnsc_mode, f';value{g_value_num}', ztxtscript, 1)# 640x480
            else:
                ztxtscript = re.sub(
                    newnsc_mode, f';mode{newnsc_search.group(2)},value{g_value_num}', ztxtscript, 1)# 通常時

        else:
            raise ValueError(i18n.t('ui.Unsupported_resolution'))

    return script_resolution, override_resolution, ztxtscript


def onsscript_check_image(ztxtscript: str):

    # アルファベット小文字変換
    ztxtscript = lower_AtoZ(ztxtscript)

    # 画像表示命令抽出
    imgdict = {
        # カーソル類は最初から書いとく
        Path(r'cursor0.bmp'): {'trans': 'l', 'part': '3'},
        Path(r'cursor1.bmp'): {'trans': 'l', 'part': '3'},
        Path(r'doncur.bmp'): {'trans': 'l', 'part': '1'},
        Path(r'doffcur.bmp'): {'trans': 'l', 'part': '1'},
        Path(r'uoncur.bmp'): {'trans': 'l', 'part': '1'},
        Path(r'uoffcur.bmp'): {'trans': 'l', 'part': '1'},
    }

    # [0]が命令文/[3]が(パスの入っている)変数名/[5]が透過形式/[6]が分割数/[8]が相対パス - [3]か[8]はどちらかのみ代入される
    immode_dict_tup = re.findall(
        r'(ld)[\t\s]+([lcr])[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")[\t\s]*,[\t\s]*[0-9]+', ztxtscript)  # ld
    # setcursor系
    immode_dict_tup += re.findall(
        r'((abs)?setcursor)[\t\s]+%?.+?[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")([\t\s]*,[\t\s]*(([0-9]{1,3})|(%.+?))){1,3}', ztxtscript)
    # lsp系
    immode_dict_tup += re.findall(
        r'(lsp(h)?)[\t\s]+%?.+?[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")([\t\s]*,[\t\s]*(([0-9]{1,3})|(%.+?))){1,3}', ztxtscript)
    # lsp2系
    immode_dict_tup += re.findall(
        r'(lsph?2(add|sub)?)[\t\s]+%?.+?[\t\s]*,[\t\s]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")(([\t\s]*,[\t\s]*((-?[0-9]{1,3})|(%.+?))){1,6})?', ztxtscript)

    # 変数に画像表示命令用の文字列突っ込んである場合があるのでそれ抽出
    # [0]が命令文/[1]が変数名/[3]が透過形式/[4]が分割数/[6]が相対パス
    immode_var_tup = re.findall(# パスの入ったmov及びstralias
        r'(stralias|mov)[\t\s]*(\$?[A-Za-z0-9_]+?)[\t\s]*,[\t\s]*"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)"', ztxtscript)

    # [0]が相対パス
    immode_dict2_tup = re.findall(
        r'bg[\t\s]+"(.+?)"[\t\s]*,[\t\s]*([0-9]+|%[A-z0-9]+)', ztxtscript)  # 背景

    # ここにsetwindow画像パス抽出正規表現セット - 未実装
    # [2]がx、[5]がy、[9]が透過方式、[10]が相対パス
    setwindow_re_tup = re.findall(
        r'setwindow3?\s+(\s*(([0-9]+)|%[A-z0-9$]+)\s*,)(\s*(([0-9]+)|%[A-z0-9$]+)\s*,)(\s*([0-9]+|%[A-z0-9$]+)\s*,){9}\s*"(:([alrc]);)?(.+?)"\s*,', ztxtscript)

    for l in immode_dict_tup:
        # 抽出したタプルからパスを取得
        if (bool(l[8]) and (not r'$' in l[8])):
            p = l[8]
        elif (bool(l[3]) and (not r'$' in l[3])):
            p = l[3]
        else:
            p = ''

        if p:
            imgdict[Path(p)] = {}  # とりあえず辞書作成
            if (l[5]):
                imgdict[Path(p)]['trans'] = l[5]  # 透過モード
            if (l[6]):
                imgdict[Path(p)]['part'] = l[6]  # 表示時画像分割数

    for l in immode_var_tup:
        # 抽出したタプルからパスを取得
        if (bool(l[6]) and (not r'$' in l[6])):
            p = l[6]
        else:
            p = ''

        if p:
            imgdict[Path(p)] = {}  # とりあえず辞書作成
            if (l[3]):
                imgdict[Path(p)]['trans'] = l[3]  # 透過モード
            if (l[4]):
                imgdict[Path(p)]['part'] = l[4]  # 表示時画像分割数

    for l in immode_dict2_tup:
        # 抽出したタプルからパスを取得
        if l[0]:
            p = l[0]
        else:
            p = ''

        if p:
            imgdict[Path(p)] = {}  # とりあえず辞書作成
            imgdict[Path(p)]['trans'] = 'c'  # 透過モード
            imgdict[Path(p)]['part'] = '1'  # 表示時画像分割数

    for l in setwindow_re_tup:
        # 抽出したタプルからパスを取得
        p = l[10] if bool(l[10]) else ''

        if p:
            winx = l[2] if bool(l[2]) else 0
            winy = l[5] if bool(l[5]) else 0

            imgdict[Path(p)] = {}  # とりあえず辞書作成
            if (l[9]):
                imgdict[Path(p)]['trans'] = l[9]  # 透過モード
            imgdict[Path(p)]['setwinpos'] = (winx, winy)

    return imgdict


def onsscript_check_bgm(ztxtscript: str):

    # アルファベット小文字変換
    ztxtscript = lower_AtoZ(ztxtscript)

    # bgm再生命令抽出
    bgmlist = []
    for a in re.findall(r'(bgm|mp3loop)[\t\s]+"(.+?)"', ztxtscript):
        bgmlist.append(Path(a[1]))  # txt内の音源の相対パスを格納
    return set(bgmlist)


def onsscript_check_vid(ztxtscript: str):

    # アルファベット小文字変換
    ztxtscript = lower_AtoZ(ztxtscript)

    # 動画再生命令抽出
    vidlist = []
    for a in re.findall(r'(mpegplay|avi)[\t\s]+"(.+?)"', ztxtscript):
        vidlist.append(Path(a[1]))  # txt内の動画の相対パスを格納
    return set(vidlist)


def onsscript_check_txtmodify_adddefsub(ztxtscript: str, pre_txt: str, aft_txt: str):

    ztxtscript_old = ztxtscript

    # game命令追加
    ztxtscript = re.sub(r'[\n\t\s]*[Gg][Aa][Mm][Ee][\t\s]*(;(.*?))?[\t\s]*\n',
                        f'\n{pre_txt}\ngame\n{aft_txt}\n', ztxtscript, 1)

    if (ztxtscript == ztxtscript_old):
        raise ValueError(i18n.t('ui.game_command_addition_error'))

    return ztxtscript


def onsscript_check_txtmodify(values: dict, values_ex: dict, ztxtscript: str, override_resolution: list):
    hardware = values['hardware']
    vid_movfmt_radio = values['vid_movfmt_radio']
    etc_0txtnbz_radio = values['etc_0txtnbz_radio']
    etc_0txtavitompegplay = values['etc_0txtavitompegplay']
    etc_0txtnoscreenshot = values['etc_0txtnoscreenshot']

    # ns2/ns3命令は全部nsaへ
    ztxtscript = re.sub(
        r'\n[\t\s]*[Nn][Ss][2|3][\t\s]*\n', r'\nnsa\n', ztxtscript)

    # numalias命令を追加
    numalias_list = [4080, 4081, 4082, 4083, 4084, 4085,
                     4086, 4087, 4088, 4089]  # ここ将来的にはGUIで設定できるようにしたい
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias0,{numalias_list[0]}', '')
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias1,{numalias_list[1]}', '')
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias2,{numalias_list[2]}', '')
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias3,{numalias_list[3]}', '')
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias4,{numalias_list[4]}', '')
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias5,{numalias_list[5]}', '')
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias6,{numalias_list[6]}', '')
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias7,{numalias_list[7]}', '')
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias8,{numalias_list[8]}', '')
    ztxtscript = onsscript_check_txtmodify_adddefsub(
        ztxtscript, f'numalias multiconverteralias9,{numalias_list[9]}', '')

    # nbz変換設定
    if (etc_0txtnbz_radio == i18n.t('var.replace_all_nbz_to_wav')):
        ztxtscript = re.sub(r'\.[Nn][Bb][Zz]', r'.wav', ztxtscript)
    elif (etc_0txtnbz_radio == i18n.t('var.convert_and_keep_both')):
        pass
    else:
        raise ValueError(i18n.t('ui.nbz_conversion_setting_error'))
    
    # avi命令→mpegplay命令変換
    if (vid_movfmt_radio == i18n.t('var.do_not_convert')): # そもそも動画を「変換しない」にしている
        ztxtscript = onsscript_check_txtmodify_adddefsub(# なら全部無力化
            ztxtscript, 'defsub avi', '*avi\ngetparam $multiconverteralias0,%multiconverteralias0:return')
        ztxtscript = onsscript_check_txtmodify_adddefsub(
            ztxtscript, 'defsub mpegplay', '*mpegplay\ngetparam $multiconverteralias0,%multiconverteralias0:return')
    elif (etc_0txtavitompegplay == i18n.t('var.use_function_override')) or (vid_movfmt_radio == i18n.t('var.numbered_images')): # 利用する(関数上書き) または 動画「連番画像」利用時
        ztxtscript = onsscript_check_txtmodify_adddefsub(# avi命令をmpegplay命令に変換
            ztxtscript, 'defsub avi', '*avi\ngetparam $multiconverteralias0,%multiconverteralias0:mpegplay $multiconverteralias0,%multiconverteralias0:return')
    elif (etc_0txtavitompegplay == i18n.t('var.use_regex_replace')): # 利用する(正規表現置換)
        ztxtscript = re.sub(
            r'([\n|\t| |:])[Aa][Vv][Ii][\t\s]+"(.+?)",[\t\s]*([0|1]|%[0-9]+)', r'\1mpegplay "\2",\3', ztxtscript)
    elif (etc_0txtavitompegplay == i18n.t('var.do_not_use')):  # 利用しない
        pass
    else:  # 未選択エラー
        raise ValueError(i18n.t('ui.avi_conversion_setting_error'))

    # savescreenshot命令無効化
    if (etc_0txtnoscreenshot == i18n.t('var.use_function_override')):  # 利用する(関数上書き)
        ztxtscript = onsscript_check_txtmodify_adddefsub(
            ztxtscript, 'defsub savescreenshot', '*savescreenshot\nreturn')  # savescreenshot命令を無効化
        ztxtscript = onsscript_check_txtmodify_adddefsub( # savescreenshot2命令を無効化
            ztxtscript, 'defsub savescreenshot2', '*savescreenshot2\nreturn')
    elif (etc_0txtnoscreenshot == i18n.t('var.use_regex_replace')):  # 利用する(正規表現置換)
        ztxtscript = re.sub(
            r'([:|\n])[Ss][Aa][Vv][Ee][Ss][Cc][Rr][Ee][Ee][Nn][Ss][Hh][Oo][Tt]2?[\t\s]+"(.+?)"[\t\s]*([:|\n])', r'\1wait 0\3', ztxtscript)
    elif (etc_0txtnoscreenshot == i18n.t('var.do_not_use')):  # 利用しない
        pass
    else:  # 未選択エラー
        raise ValueError(i18n.t('ui.savescreenshot_setting_error'))

    # 最大回想ページ数設定
    if values['etc_0txtmaxkaisoupage_chk']:
        ztxtscript = onsscript_check_txtmodify_adddefsub(# 本当はdefsub追加用の関数だが流用
            ztxtscript, f'maxkaisoupage {values['etc_0txtmaxkaisoupage_num']}', '')

    # 最大セーブ数設定
    if values['etc_0txtoverwritesavenumber_chk']:
        ztxtscript = onsscript_check_txtmodify_adddefsub(# 本当はdefsub追加用の関数だが流用
            ztxtscript, f'savenumber {values['etc_0txtoverwritesavenumber_num']}', '')

    # setwindowのフォントサイズ変更(PSP解像度無視変換時は無効)
    if values['etc_0txtsetwindowbigfont_chk'] and (not override_resolution):

        # 倍率計算
        fontper = values_ex['output_resolution'][1] / \
            values_ex['script_resolution'][1]

        # 倍率が1未満の時のみ処理
        if fontper < 1:

            # txt内のsetwindow命令を格納 - [0]命令文前部分/[2]横文字数/[3]縦文字数/[4]横文字サイズ/[5]縦文字サイズ/[6]横文字間隔/[7]縦文字間隔/[8]命令文後部分
            setwindow_re_fnttup = re.findall(
                r'([Ss][Ee][Tt][Ww][Ii][Nn][Dd][Oo][Ww]3?[\t\s]+([0-9]{1,},){2})([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),(([0-9]{1,},){3}(.+?)(,[0-9]{1,}){2,4})', ztxtscript)

            for v in set(setwindow_re_fnttup):

                txtmin = math.ceil(10 / fontper)
                nummin = min(int(v[4]), int(v[5]))

                # 表示時10pxを下回りそうな場合 - ちなみに10pxはMSゴシックで漢字が潰れない最低サイズ
                if txtmin > nummin:

                    # 文字の縦横サイズが違う可能性を考え別に処理 - もちろん縦横比維持
                    # 横文字サイズ(拡大)
                    v4rp = str(int(txtmin * (int(v[4]) / nummin)))
                    # 縦文字サイズ(拡大)
                    v5rp = str(int(txtmin * (int(v[5]) / nummin)))
                    # 横文字間隔(縮小)
                    v6rp = str(int(int(v[6]) * (nummin / int(v4rp))))
                    # 縦文字間隔(縮小)
                    v7rp = str(int(int(v[7]) * (nummin / int(v5rp))))

                    # 横に表示できる最大文字数を(文字を大きくした分)減らす - 見切れるのを防ぐため縦はそのまま
                    # v2rp = str( int( int(v[2]) * ( int(v[4]) + int(v[6]) ) / ( int(v4rp) + int(v6rp) ) ) )

                    sw = (v[0] + v[2] + ',' + v[3] + ',' + v[4] +
                          ',' + v[5] + ',' + v[6] + ',' + v[7] + ',' + v[8])
                    sw_re = (v[0] + v[2] + ',' + v[3] + ',' + v4rp +
                             ',' + v5rp + ',' + v6rp + ',' + v7rp + ',' + v[8])

                    ztxtscript = ztxtscript.replace(sw, sw_re)

    # okcancelboxをmovで強制ok
    if values['etc_0txtskipokcancelbox_chk']:
        ztxtscript = re.sub(
            r'([\n|\t| |:])[Oo][Kk][Cc][Aa][Nn][Cc][Ee][Ll][Bb][Oo][Xx][\t\s]+%([A-z0-9_]+?),', r'\1mov %\2,1 ;', ztxtscript)

    # yesnoboxをmovで強制yes
    if values['etc_0txtskipyesnobox_chk']:
        ztxtscript = re.sub(
            r'([\n|\t| |:])[Yy][Ee][Ss][Nn][Oo][Bb][Oo][Xx][\t\s]+%([A-z0-9_]+?),', r'\1mov %\2,1 ;', ztxtscript)

    # rnd2を自作命令multiconverterrnd2def(連番)に変換
    if values['etc_0txtrndtornd2_chk']:
        for i, r in enumerate(re.findall(r'(([\n|\t| |:])[Rr][Nn][Dd]2[\t\s]+(%[A-z0-9_]+)[\t\s]*,[\t\s]*([0-9]+|%[A-z0-9_]+)[\t\s]*,[\t\s]*([0-9]+|%[A-z0-9_]+))', ztxtscript)):
            ztxtscript = onsscript_check_txtmodify_adddefsub(
                ztxtscript, f'defsub multiconverterrnd2def{i}', f'*multiconverterrnd2def{i}\nrnd {r[2]},{r[4]}+1-{r[3]}:add {r[2]},{r[3]}:return')
            ztxtscript = re.sub(
                r[0], f'{r[1]}multiconverterrnd2def{i}', ztxtscript, 1)

    # textgosub無効化
    if values['etc_0txtdisabletextgosub_chk']:
        textgosub_regex = r'([:|\n])[Tt][Ee][Xx][Tt][Gg][Oo][Ss][Uu][Bb][\t\s]+\*[A-z0-9_]+[\t\s]*([:|\n])'
        rmenu_regex = r'([Rr][Mm][Ee][Nn][Uu][\t\s]+"(.+?),?[\t\s]*([:|\n]))'
        rmenucm_regex = r';([Rr][Mm][Ee][Nn][Uu][\t\s]+"(.+?),?[\t\s]*([:|\n]))'

        if re.search(textgosub_regex, ztxtscript):
            # 本当は定義節にwaitっておかしいんだけど動くのでそのまま
            ztxtscript = re.sub(textgosub_regex, r'\1wait 0\2', ztxtscript)

            # rmenuがコメントアウトされてるなら復活
            if re.search(rmenucm_regex, ztxtscript):
                ztxtscript = re.sub(rmenu_regex, r'\1', ztxtscript)

            # そもそもrmenuがない場合は作成
            elif not re.search(rmenu_regex, ztxtscript):
                ztxtscript = onsscript_check_txtmodify_adddefsub(
                    ztxtscript, 'rmenu "セーブ",save,"ロード",load,"スキップ",skip,"タイトル",reset', '')

    # 連番画像利用時mpegplay命令
    if (values['vid_movfmt_radio'] == i18n.t('var.numbered_images')):
        # 参考: https://web.archive.org/web/20110308215321fw_/http://blog.livedoor.jp/tormtorm/archives/51356258.html

        # btndef+blt選択
        if (values['vid_renbanprintfmt_radio'] == 'btndef+blt'):
            if hardware == 'PSVITA':
                bltx1 = math.ceil(
                    540 / values_ex['output_resolution'][1] * values_ex['output_resolution'][0])
                blty1 = 544

            else:
                bltx1 = values_ex['script_resolution'][0]
                blty1 = values_ex['script_resolution'][1]

            bltx2 = math.ceil(bltx1 * values_ex['renbanresper'])
            blty2 = math.ceil(blty1 * values_ex['renbanresper'])

            renbanprintline = f'btndef $11+$%3+$12+$14:blt 0,0,{bltx1},{blty1},0,0,{bltx2},{blty2}'
        
        # bg選択(実質)
        else:
            renbanprintline = f'bg $11+$%3+$12+$14,1'

        ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'defsub mpegplay', f'''*mpegplay
saveoff
mov %multiconverteralias0,%0 :mov %multiconverteralias1,%1 :mov %multiconverteralias2,%2 :mov %multiconverteralias3,%3 :mov %multiconverteralias4,%4 
mov %multiconverteralias5,%5 :mov %multiconverteralias6,%6 :mov %multiconverteralias7,%7 :mov %multiconverteralias8,%8 :mov %multiconverteralias9,%9 
mov $multiconverteralias0,$10:mov $multiconverteralias1,$11:mov $multiconverteralias2,$12:mov $multiconverteralias3,$13:mov $multiconverteralias4,$14:mov $multiconverteralias5,$15
getparam $13,%9:fileexist %0,$13+"/00000.jpg"
fileexist %1,"_DISABLED_VIDEO"
if %1==1 mov $13,$multiconverteralias3:mov %9,%multiconverteralias9:mov %1,%multiconverteralias1:saveon:return
fileexist %1,$13+"/_DISABLED_VIDEO"
if %1==1 mov $13,$multiconverteralias3:mov %9,%multiconverteralias9:mov %1,%multiconverteralias1:saveon:return
if %0==1 mov $14,".jpg"
if %0!=1 mov $14,".png"
mov $11,$13:add $11,"/":mov %6,5:mov $15,""
for %4=7 to 1 step -1:itoa $10,%4:for %5=0 to 9
itoa $12,%5:fileexist %7,$11+"keta"+$10+"_"+$12
if %7==1 add $15,$12:break
next:next:atoi %2,$15:for %4=1 to %6:mov $%4,"":next
*count
dec %6:for %4=1 to %6:add $%4,"0":next
if %6!=1 goto *count
mov %0,5000
*movie_count1
itoa $12,%0:len %3,$12:fileexist %4,$11+$%3+$12+$14
if %4==1 add %0,5000:goto *movie_count1
mov %1,0
*movie_count2
mov %8,(%1+%0)/2:itoa $12,%8:len %3,$12:fileexist %4,$11+$%3+$12+$14:mov %%4,%8+1*%4-1*(1-%4)
if %1!=%0 goto *movie_count2
if %9==1 lr_trap *movie_end
bgmonce $11+"audio.mus":resettimer
*movie_loop
gettimer %1
if %2<=%1 goto *movie_end
itoa $12,%0*%1/%2
if $12==$10 waittimer 0:goto *movie_loop
mov $10,$12:len %3,$12:{renbanprintline}:goto *movie_loop
*movie_end
lr_trap off:ofscpy:bg black,1:stop
mov %0 ,%multiconverteralias0:mov %1 ,%multiconverteralias1:mov %2 ,%multiconverteralias2:mov %3 ,%multiconverteralias3:mov %4 ,%multiconverteralias4
mov %5 ,%multiconverteralias5:mov %6 ,%multiconverteralias6:mov %7 ,%multiconverteralias7:mov %8 ,%multiconverteralias8:mov %9 ,%multiconverteralias9
mov $10,$multiconverteralias0:mov $11,$multiconverteralias1:mov $12,$multiconverteralias2:mov $13,$multiconverteralias3:mov $14,$multiconverteralias4:mov $15,$multiconverteralias5
saveon:return''')

    # nsa命令追記
    ztxtscript = onsscript_check_txtmodify_adddefsub(ztxtscript, 'nsa', '')

    return ztxtscript


def set_output_resolution(values: dict, values_ex: dict, override_resolution: list):
    preferred_resolution = values['preferred_resolution']
    select_resolution = values_ex['select_resolution']
    script_resolution = values_ex['script_resolution']

    # 最終解像度取得
    if select_resolution:
        if override_resolution:
            output_resolution = override_resolution  # 解像度無視変換時

        else:
            if (preferred_resolution == i18n.t('var.high_resolution_priority')):
                output_resolution = select_resolution[0]
            else:
                output_resolution = select_resolution[1]

    # その他
    else:
        output_resolution = script_resolution

    return output_resolution


def onsscript_check(values: dict, values_ex: dict):
    hardware = values['hardware']

    # 0.txtのテキスト取得
    ztxtscript = values_ex['0txtscript']

    # *defineがない時
    if not re.search(r'\*define', ztxtscript):
        raise Exception('0.txtの復号化に失敗しました')

    # 変換済み簡易チェック
    if re.search(r'Converted by "ONScripter Multi Converter', ztxtscript):
        raise Exception('このファイルは既に変換済みです')

    # PSP用解像度無視変換フラグ
    if (hardware == 'PSP') and (r'<ONS_RESOLUTION_CHECK_DISABLED>' in ztxtscript):
        override_resolution = (480, 272)
    else:
        override_resolution = ()

    # 解像度無視変換時setwindow画像描画バグ対策無効化(そのままだと解像度取得ミスって見切れる)
    if override_resolution:
        values_ex['setwinimgbug'] = False

    # 解像度表記抽出&新表記が読めないPSP用変換
    values_ex['script_resolution'], override_resolution, ztxtscript = onsscript_check_resolution(
        values, values_ex, ztxtscript, override_resolution)

    # 元作品解像度が存在しない場合(=別エンジンONSコンバータを事前に使用していない時)0.txtから抽出した解像度をvalues_exに格納
    if not values_ex.get('input_resolution'):
        values_ex['input_resolution'] = values_ex['script_resolution']

    # 最終解像度取得
    values_ex['output_resolution'] = set_output_resolution(
        values, values_ex, override_resolution)

    # 画像表示命令抽出
    values_ex['imgdict'] = onsscript_check_image(ztxtscript)

    # bgm再生命令抽出
    values_ex['bgmlist'] = onsscript_check_bgm(ztxtscript)

    # 動画再生命令抽出
    values_ex['vidlist'] = onsscript_check_vid(ztxtscript)

    # savedir抽出
    try:
        values_ex['savedir_path'] = (
            re.search(r'\n[\t| ]*savedir[\t| ]+"(.+?)"', lower_AtoZ(ztxtscript)))[1]
    except:
        values_ex['savedir_path'] = False

    # 画像が初期設定でどのような透過指定で扱われるかを代入
    try:
        values_ex['imgtransmode'] = (re.search(# transmode命令があればそれ(の最初の文字)を採用
            r'\n[\t| ]*transmode[\t| ]+(leftup|copy|alpha)', lower_AtoZ(ztxtscript)))[1][0]
    except:
        # 見つからないなら初期値leftup…のはずだがlだとタグ付けミスった時盛大に破綻するので仕方なくalpha
        values_ex['imgtransmode'] = 'a'

    # 0.txt関連はここで編集
    ztxtscript = onsscript_check_txtmodify(
        values, values_ex, ztxtscript, override_resolution)

    # 最終的にvalues_exに格納
    values_ex['0txtscript'] = ztxtscript

    return values_ex
