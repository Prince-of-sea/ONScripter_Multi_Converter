#!/usr/bin/env python3
from hardwarevalues_config import gethardwarevalues
from conversion import convert_start
from utils import get_titlesettingfull

def cli_main(version: str, hw_key: str, input_dir_param: str, output_dir_param: str, title_setting_param: str):

	#個別設定名登録(除外は前段階でやってるので気にしなくておｋ)
	title_setting = get_titlesettingfull(title_setting_param)

	#タイトル表示
	print(
		f'入力元: {input_dir_param}\n'
		f'出力先: {output_dir_param}\n'
		f'ハード: {hw_key}\n'
		f'個別設定: {title_setting}\n'
		'------------------------------------------------------------'\
	)

	#values作成
	values = {
		'input_dir': input_dir_param,
		'output_dir': output_dir_param,
		'hardware': hw_key,
		'version': version,
		'title_setting': title_setting,
	}

	#とりあえず初期値突っ込んどく
	values.update( gethardwarevalues(values['hardware'], 'values_default') )

	#変換開始
	convert_start(values)

	return