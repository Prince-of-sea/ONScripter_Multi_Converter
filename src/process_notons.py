#!/usr/bin/env python3
from pathlib import Path

import notons2ons


def get_titledict():
	d = {}
	#ここにタイトル追加 - ブランドABC/あいうえお読み順(どっち表記かは批評空間基準で)、発売日順
	d['[ACTRESS]虹を見つけたら教えて。'] = notons2ons.ACTGS2ONS_Actress_Nijimite.title_info()
	d['[CHARON]掴め、人生の右打ち!GOGO全回転 嵐を呼ぶ!炎のパチンカスロード'] = notons2ons.TYRANO2ONS_CHARON_Pachi.title_info()
	d['[CUFFS]ワンコとリリー (パッケージ版不可)'] = notons2ons.KIRIKIRI2ONS_CUFFS_wankor.title_info()
	d['[Liar-soft]SEVEN-BRIDGE'] = notons2ons.RSC2ONS_Liar_SB.title_info()
	d['[Moviendo]処女回路'] = notons2ons.KIRIKIRI2ONS_Moviendo_otomec.title_info()
	d['[Noesis]ラブesエム'] = notons2ons.IGS2ONS_Noesis_loveesm.title_info()
	d['[raiL-soft]霞外籠逗留記'] = notons2ons.RSC2ONS_raiL_kagerou.title_info()
	d['[Supplement Time]未来のキミと、すべての歌に―'] = notons2ons.KIRIKIRI2ONS_ST_miku.title_info()
	d['[アパタイト]祖母シリーズ汎用 (〜2020)'] = notons2ons.KIRIKIRI2ONS_APTIT_sobo.title_info()
	d['[ケロQ]終ノ空'] = notons2ons.DIR2ONS_KeroQ_FinalSky.title_info()
	d['[コンプリーツ]ママとの甘い性活II'] = notons2ons.KIRIKIRI2ONS_COMP_mama2.title_info()
	d['[ステージ☆なな]冬のポラリス'] = notons2ons.MJO2ONS_NANA_Polaris.title_info()
	d['[羊おじさん倶楽部]魔女魔少魔法魔'] = notons2ons.KIRIKIRI2ONS_unclesheep_mgirlm.title_info()
	d['[夜のひつじ]孤独に効く百合'] = notons2ons.KIRIKIRI2ONS_yorunohitsuji_kodoyuri.title_info()
	d['[るび様を崇める会]ご主人様、セイラに夢みたいないちゃラブご奉仕させていただけますか'] = notons2ons.TYRANO2ONS_Rubisama_seilove.title_info()
	
	return d


def pre_convert(values: dict, values_ex: dict, pre_converted_dir: Path):

	match values['title_setting']:
		#ここにタイトル追加 - 上のやつと順番合わせたほうが良いかも
		case '[ACTRESS]虹を見つけたら教えて。': notons2ons.ACTGS2ONS_Actress_Nijimite.main(values, values_ex, pre_converted_dir)
		case '[CHARON]掴め、人生の右打ち!GOGO全回転 嵐を呼ぶ!炎のパチンカスロード': notons2ons.TYRANO2ONS_CHARON_Pachi.main(values, values_ex, pre_converted_dir)
		case '[CUFFS]ワンコとリリー (パッケージ版不可)': notons2ons.KIRIKIRI2ONS_CUFFS_wankor.main(values, values_ex, pre_converted_dir)
		case '[Liar-soft]SEVEN-BRIDGE': notons2ons.RSC2ONS_Liar_SB.main(values, values_ex, pre_converted_dir)
		case '[Moviendo]処女回路': notons2ons.KIRIKIRI2ONS_Moviendo_otomec.main(values, values_ex, pre_converted_dir)
		case '[Noesis]ラブesエム': notons2ons.IGS2ONS_Noesis_loveesm.main(values, values_ex, pre_converted_dir)
		case '[raiL-soft]霞外籠逗留記': notons2ons.RSC2ONS_raiL_kagerou.main(values, values_ex, pre_converted_dir)
		case '[Supplement Time]未来のキミと、すべての歌に―': notons2ons.KIRIKIRI2ONS_ST_miku.main(values, values_ex, pre_converted_dir)
		case '[アパタイト]祖母シリーズ汎用 (〜2020)': notons2ons.KIRIKIRI2ONS_APTIT_sobo.main(values, values_ex, pre_converted_dir)
		case '[ケロQ]終ノ空': notons2ons.DIR2ONS_KeroQ_FinalSky.main(values, values_ex, pre_converted_dir)
		case '[コンプリーツ]ママとの甘い性活II': notons2ons.KIRIKIRI2ONS_COMP_mama2.main(values, values_ex, pre_converted_dir)
		case '[ステージ☆なな]冬のポラリス': notons2ons.MJO2ONS_NANA_Polaris.main(values, values_ex, pre_converted_dir)
		case '[羊おじさん倶楽部]魔女魔少魔法魔': notons2ons.KIRIKIRI2ONS_unclesheep_mgirlm.main(values, values_ex, pre_converted_dir)
		case '[夜のひつじ]孤独に効く百合': notons2ons.KIRIKIRI2ONS_yorunohitsuji_kodoyuri.main(values, values_ex, pre_converted_dir)
		case '[るび様を崇める会]ご主人様、セイラに夢みたいないちゃラブご奉仕させていただけますか': notons2ons.TYRANO2ONS_Rubisama_seilove.main(values, values_ex, pre_converted_dir)
		case _: raise ValueError('title_setting error.')

	return