#!/usr/bin/env python3
# windows only
import click

from hardwarevalues_config import gethardwarevalues_full
from ui_gui import gui_main
from ui_cli import cli_main

@click.command()
@click.option('-hw', '--hardware', type=click.Choice(list(gethardwarevalues_full().keys()), case_sensitive=False),
			  default=str(list(gethardwarevalues_full().keys())[0]), prompt=False, help='変換先ハードウェアを指定します')
@click.option('-cl', '--use_cli', is_flag=True, default=False, help='コマンドラインインターフェースを有効化します')
@click.option('-i', '--input_dir', type=click.Path(), default='', prompt=False, help='入力フォルダのパスを指定します')
@click.option('-o', '--output_dir', type=click.Path(), default='', prompt=False, help='出力フォルダのパスを指定します')


def main(use_cli, hardware, input_dir, output_dir):
	"""ONS向け画像/音源/動画&シナリオ変換ツール"""
	version = '2.1.2'

	if use_cli: cli_main(version, hardware, input_dir, output_dir)
	else: gui_main(version, hardware, input_dir, output_dir)


if __name__ == "__main__":
	main()