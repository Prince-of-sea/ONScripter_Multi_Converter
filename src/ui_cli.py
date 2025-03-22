#!/usr/bin/env python3
from hardwarevalues_config import gethardwarevalues
from conversion import convert_start
from utils import value_setting_update, get_titlesettingfull

def cli_main(version: str, charset_param: str, hw_key: str, input_dir_param: str, output_dir_param: str, title_setting_param: str, value_setting_param: str):

	#個別設定名登録(除外は前段階でやってるので気にしなくておｋ)
	title_setting = get_titlesettingfull(title_setting_param)

	#タイトル表示
	print(
		f'input directory: {input_dir_param}\n'
		f'output directory: {output_dir_param}\n'
		f'hardware: {hw_key}\n'
		f'title: {title_setting}\n'
		'------------------------------------------------------------'\
	)

	#文字コード指定時は個別設定は指定できない
	if (charset_param != 'cp932') and (title_setting_param != ''):
		raise Exception('If character encoding is specified, “title_setting” cannot be used.')

	#指定された文字コードがハードウェアに対応しているか確認
	if not (charset_param in gethardwarevalues(hw_key, 'values_ex')['support_charset']):	
		raise Exception('The specified character set is not supported by this hardware.')

	#values作成
	values = {
		'useGUI': False,
		'charset': charset_param,
		'input_dir': input_dir_param,
		'output_dir': output_dir_param,
		'hardware': hw_key,
		'version': version,
		'title_setting': title_setting,
	}

	#ハードウェア値取得
	values_default = gethardwarevalues(hw_key, 'values_default')
	values_default = value_setting_update(values_default, value_setting_param)

	#とりあえず初期値突っ込んどく
	values.update(values_default)

	#変換開始
	convert_start(values)

	return