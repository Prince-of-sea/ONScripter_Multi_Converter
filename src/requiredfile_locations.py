#!/usr/bin/env python3
from pathlib import Path
import subprocess as sp
import sys

from utils2 import subprocess_args  # utils呼ぶと相互importエラー出るので


# 同一階層のパスを変数へ代入
__same_hierarchy = Path(sys.argv[0]).parent

# ファイルパス辞書
requiredfile_locations_dict = {
    # 必須
    'GARbro_GUI': Path(__same_hierarchy / 'tools' / 'Garbro_console' / 'GARbro.GUI.exe'),
    'GARbro': Path(__same_hierarchy / 'tools' / 'Garbro_console' / 'GARbro.Console.exe'),
    'smjpeg_encode': Path(__same_hierarchy / 'tools' / 'smjpeg_encode.exe'),
    'nsaed': Path(__same_hierarchy / 'tools' / 'nsaed.exe'),

    # 'PATH'でもおｋ
    'ffmpeg': Path(__same_hierarchy / 'tools' / 'ffmpeg.exe'),
    'ffprobe': Path(__same_hierarchy / 'tools' / 'ffprobe.exe'),

    # 個別変換時に必要
    'gscScriptCompAndDecompiler-cli': Path(__same_hierarchy / 'tools' / 'gscScriptCompAndDecompiler.exe'),
    'DirectorCastRipper_D10': Path(__same_hierarchy / 'tools' / 'DirectorCastRipper_D10' / 'DirectorCastRipper.exe'),
    'igscriptD': Path(__same_hierarchy / 'tools' / 'igscriptD.exe'),
    'Kikiriki': Path(__same_hierarchy / 'tools' / 'Kikiriki' / 'Kikiriki.exe'),
    'mjdisasm': Path(__same_hierarchy / 'tools' / 'mjdisasm.exe'),
}
################################################################################


def location(key: str) -> Path:
    return requiredfile_locations_dict[key]


def location_env(key: str) -> Path:
    if (requiredfile_locations_dict[key]).exists():
        return requiredfile_locations_dict[key]
    else:
        return key


def location_list(key_list: list) -> list:
    result_list = []
    for k in key_list:
        result_list.append(requiredfile_locations_dict[k])
    return result_list


def exist(key: str) -> bool:
    return bool(requiredfile_locations_dict.get(key).exists())


def exist_env(key: str) -> bool:
    if (requiredfile_locations_dict[key]).exists():
        return True
    else:
        try:
            sp.run(key, **subprocess_args())
        except:
            return False
        else:
            return True


def exist_all(key_list: list) -> bool:
    result_list = []
    for k in key_list:
        result_list.append(bool(requiredfile_locations_dict.get(k).exists()))
    return not (False in result_list)  # 一個でもFalseがあったらFalse


def exist_list(key_list: list) -> list:
    result_list = []
    for k in key_list:
        result_list.append(bool(requiredfile_locations_dict.get(k).exists()))
    return result_list

# 将来的には旧verにあった"何が足りないか"を指定する機能もほしいなって
