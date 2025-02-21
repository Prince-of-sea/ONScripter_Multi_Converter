#!/usr/bin/env python3
from hardwarevalues_config import gethardwarevalues
from conversion import convert_start


def cli_main(version: str, hardware: str, input_dir: str, output_dir: str):
	#とりあえずタイトル
	window_title = f'ONScripter Multi Converter for {hardware} ver.{version}'

	#タイトル表示
	print('\n------------------------------------------------------------\n' + window_title +'\n------------------------------------------------------------')

	#values作成
	values = {
		'input_dir': input_dir,
		'output_dir': output_dir,
		'hardware': hardware,
		'version': version
	}

	#とりあえず初期値突っ込んどく
	values.update( gethardwarevalues(values['hardware'], 'values_default') )

	#変換開始
	convert_start(values)

	return