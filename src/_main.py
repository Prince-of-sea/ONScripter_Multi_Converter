#!/usr/bin/env python3
# windows only
import ctypes
import click
import i18n
import sys
import os

from hardwarevalues_config import gethardwarevalues_full
from process_notons import get_titledict
from utils import get_meipass
from ui_gui import gui_main
from ui_cli import cli_main


@click.command()
@click.option('-t', '--title_setting', type=click.Choice(['']+[s['cli_arg'] for s in get_titledict().values()], case_sensitive=False),
              default='', prompt=False, help='Specify individual settings for specific titles. (cp932 only)')
@click.option('-hw', '--hardware', type=click.Choice(['']+list(gethardwarevalues_full().keys()), case_sensitive=False),
              default='', prompt=False, help='Specify for which hardware to convert.')
@click.option('-lang', '--language', type=click.Choice(['', 'ja', 'zh', 'en'], case_sensitive=False),
              default='', prompt=False, help='Specify the language of the UI.')
@click.option('-chrs', '--charset', type=click.Choice(['', 'cp932', 'gbk', 'utf-8'], case_sensitive=False),
              default='', prompt=False, help='Specifies character code.')
@click.option('-i', '--input_dir', type=click.Path(), default='', prompt=False, help='Specify the path of the input folder.')
@click.option('-o', '--output_dir', type=click.Path(), default='', prompt=False, help='Specify the path of the output folder.')
@click.option('-vl', '--value_setting', type=click.STRING, default='', prompt=False, help='Specify the value setting.')
@click.option('-cl', '--use_cli', is_flag=True, default=False, help='Enable automatic conversion in the CLI.')
def main(language: str, charset: str, use_cli: bool, hardware: str, input_dir: str, output_dir: str, title_setting: str, value_setting: str):
    '''Image/sound/video & scenario conversion tool for ONScripter'''
    version = '2.4.3 alpha'

    # languageが空の場合は日本語判定
    if language == '':
        language = 'ja'

    # i18n設定
    i18n.load_path.append(get_meipass('lang'))
    i18n.set('locale', language)

    # 文字コードが空の場合はデフォルト文字コードを設定
    if (charset == '') and (i18n.t('var.default_charset')):
        charset = i18n.t('var.default_charset')

    # 文字コードがcp932以外の場合はバージョンに追記
    if (charset != 'cp932'):
        version += f' [{charset}]'

    # ハードウェアが空の場合はデフォルトハードウェアを設定
    if (hardware == ''):
        for hwk, hwv in gethardwarevalues_full().items():
            if (charset in hwv['values_ex']['support_charset']):
                hardware = hwk
                break

    # 開発版判定
    if not hasattr(sys, '_MEIPASS'):
        version += ' (dev)'

    # 起動前print
    print(
        '------------------------------------------------------------\n'
        f'ONScripter Multi Converter ver.{version}\n'
        '------------------------------------------------------------'
    )

    # 念の為統一
    input_dir = str(input_dir).replace('\\', '/')
    output_dir = str(output_dir).replace('\\', '/')

    # Windows以外はここで弾く
    if os.name != 'nt':
        raise Exception(i18n.t('ui.Cannot_be_started_on_non_Windows_systems'))

    # mutex作成
    mutex_name = "Global\\ONScripterMultiConverter"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)

    # 多重起動チェック
    if ctypes.windll.kernel32.GetLastError() == 183:
        print(i18n.t('ui.This_application_is_already_running'))

    # 起動
    elif use_cli:
        cli_main(version, charset, hardware, input_dir,
                 output_dir, title_setting, value_setting)
    else:
        gui_main(version, charset, hardware, input_dir,
                 output_dir, title_setting, value_setting)

    # 終了前print
    print('------------------------------------------------------------\n')

    # mutex解放
    ctypes.windll.kernel32.ReleaseMutex(mutex)


if __name__ == '__main__':
    main()
