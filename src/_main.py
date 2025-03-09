#!/usr/bin/env python3
# windows only
import ctypes, click, i18n, sys, os

from hardwarevalues_config import gethardwarevalues_full
from process_notons import get_titledict
from utils import get_meipass
from ui_gui import gui_main
from ui_cli import cli_main

@click.command()
@click.option('-t', '--title_setting', type=click.Choice(['']+[s['cli_arg'] for s in get_titledict().values()], case_sensitive=False),
				default='', prompt=False, help='特定タイトル向けの個別設定を指定します(Japanese language only.)')
@click.option('-hw', '--hardware', type=click.Choice(list(gethardwarevalues_full().keys()), case_sensitive=False),
				default=str(list(gethardwarevalues_full().keys())[0]), prompt=False, help='Specify for which hardware to convert.')
@click.option('-chrs', '--charset', type=click.Choice(['cp932', 'gbk'], case_sensitive=False),
				default='cp932', prompt=False, help='Specifies character code.')
@click.option('-i', '--input_dir', type=click.Path(), default='', prompt=False, help='Specify the path of the input folder.')
@click.option('-o', '--output_dir', type=click.Path(), default='', prompt=False, help='Specify the path of the output folder.')
@click.option('-cl', '--use_cli', is_flag=True, default=False, help='Enable automatic conversion in the CLI.')


def main(charset: str, use_cli: bool, hardware: str, input_dir: str, output_dir: str, title_setting: str):
	'''Image/sound/video & scenario conversion tool for ONS'''
	version = '2.3.9'

	#文字コード表示
	if (charset != 'cp932'): version += f' [{charset}]'

	#開発版判定
	if not hasattr(sys, '_MEIPASS'): version += ' (dev)'

	#i18n設定
	i18n.load_path.append(get_meipass('lang'))
	i18n.set('locale', 'ja')

	#起動前print
	print(
		'------------------------------------------------------------\n'
		f'ONScripter Multi Converter ver.{version}\n'
		'------------------------------------------------------------'
	)

	#念の為統一
	input_dir = str(input_dir).replace('\\', '/')
	output_dir = str(output_dir).replace('\\', '/')

	#Windows以外はここで弾く
	if os.name != 'nt': raise Exception(i18n.t('ui.Cannot_be_started_on_non_Windows_systems'))

	#mutex作成
	mutex_name = "Global\\ONScripterMultiConverter"
	mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)

	#多重起動チェック
	if ctypes.windll.kernel32.GetLastError() == 183: print(i18n.t('ui.This_application_is_already_running'))

	#起動
	elif use_cli: cli_main(version, charset, hardware, input_dir, output_dir, title_setting)
	else: gui_main(version, charset, hardware, input_dir, output_dir, title_setting)

	#終了前print
	print('------------------------------------------------------------\n')

	#mutex解放
	ctypes.windll.kernel32.ReleaseMutex(mutex)


if __name__ == '__main__':
	main()
