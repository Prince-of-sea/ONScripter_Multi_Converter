#!/usr/bin/env python3
# windows only
import click, os

from hardwarevalues_config import gethardwarevalues_full
from process_notons import get_titledict
from ui_gui import gui_main
from ui_cli import cli_main

@click.command()
@click.option('-t', '--title_setting', type=click.Choice(['']+[s['cli_arg'] for s in get_titledict().values()], case_sensitive=False),
				default='', prompt=False, help='特定タイトル向けの個別設定を指定します')
@click.option('-hw', '--hardware', type=click.Choice(list(gethardwarevalues_full().keys()), case_sensitive=False),
				default=str(list(gethardwarevalues_full().keys())[0]), prompt=False, help='変換先ハードウェアを指定します')
@click.option('-cl', '--use_cli', is_flag=True, default=False, help='コマンドラインでの自動変換モードを有効化します')
@click.option('-i', '--input_dir', type=click.Path(), default='', prompt=False, help='入力フォルダのパスを指定します')
@click.option('-o', '--output_dir', type=click.Path(), default='', prompt=False, help='出力フォルダのパスを指定します')


def main(use_cli, hardware, input_dir, output_dir, title_setting):
	'''ONS向け画像/音源/動画&シナリオ変換ツール'''
	version = '2.3.9'

	#起動前print
	print(
		'------------------------------------------------------------\n'\
		f'ONScripter Multi Converter for {hardware} ver.{version}\n'
		'------------------------------------------------------------'
	)

	#念の為統一
	input_dir = str(input_dir).replace('\\', '/')
	output_dir = str(output_dir).replace('\\', '/')

	#起動
	if os.name != 'nt': raise Exception('Windows以外では起動できません')
	elif use_cli: cli_main(version, hardware, input_dir, output_dir, title_setting)
	else: gui_main(version, hardware, input_dir, output_dir, title_setting)

	#終了前print
	print('------------------------------------------------------------\n')


if __name__ == '__main__':
	main()
