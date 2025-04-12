# ツールの設定 - CLI

## オプション一覧

 - **-t, --title_setting**  [actress_nijimite|charon_pachi|cuffs_wankor|...]<br>
 非ONScripterの作品を変換する、"個別設定"の初期値を設定します<br>
 変換できる作品とその設定についての詳細は、`--help`オプションで確認できます<br>

 - **-hw, --hardware** [PSP|PSVITA|Brain|Android]<br>
 ハードウェアの種類を指定します<br>
 何も指定しない場合PSPが使用されます<br>

 - **-lang, --language** [ja|zh|en]<br>
 言語を指定します<br>
 何も指定しない場合日本語が使用されます<br>
 中国語の対応が不安定なので、`zh`は使用しないことを推奨します<br>

 - **-chrs, --charset** [cp932|gbk|utf-8]<br>
 文字コードを指定します<br>
 何も指定しない場合`-lang`の指定に合わせて自動的に選択されます<br>

 - **-i, --input_dir** PATH<br>
 入力ディレクトリのパスを指定します<br>

 - **-o, --output_dir** PATH<br>
 出力ディレクトリのパスを指定します<br>

 - **-vl, --value_setting** STR<br>
 ハードごとに設定されている初期設定値を、自由に設定することができる機能です<br>
 基本は`キー名=値`で指定、複数指定は`;`で区切ります<br>
 設定する際に利用するキーは、[hardwarevalues_config.pyのハードごとに用意している辞書"values_default"内](./src/hardwarevalues_config.py)と全く同じです<br>
 　<br>
 細かい動作テストや例外処理の実装は行っていないため、<br>
 間違った値を入力すると未知のエラーが発生するおそれがあります<br>
 ある程度理解したうえで利用するようにしてください<br>

 - **-cl, --use_cli**<br>
 GUIを起動せず、CLI(CUI)での変換モードを使用します<br>
 特に確認などは行われず、そのまま自動で変換開始、終了します<br>
 バッチなどを使って変換作業を自動化する際に使ってください<br>

 - **--help**<br>
 ヘルプメッセージを表示します<br>


## 使用例
いくつかそれっぽいものを用意したので参考にしてください

#### 変換ハードの初期値をPSVITAにした状態で起動
```
ONScripter_Multi_Converter.exe -hw PSVITA
```


#### 出力先の初期値をDドライブのtempフォルダにした状態で起動
```
ONScripter_Multi_Converter.exe -o "D:/temp"
```


#### 個別設定の初期値を`[Liar-soft]SEVEN-BRIDGE`にした状態で起動
```
ONScripter_Multi_Converter.exe -t liar_sb
```


#### BGMチャンネル数の初期値をモノラルにして起動
```
ONScripter_Multi_Converter.exe -vl "aud_bgmch_radio=モノラル"
```


#### BGMと効果音/ボイスの圧縮先の初期値をarc.nsaにして起動
```
ONScripter_Multi_Converter.exe -vl "etc_filecompbgm_nsa=arc.nsa;etc_filecompse_nsa=arc.nsa"
```


#### 英語UIで日本語作品変換モードを起動
```
ONScripter_Multi_Converter.exe -lang en -chrs cp932
```


#### CLIモード有効で、インストール済みの「うみねこのなく頃に散(NScripter作品)」を佐藤裕也のデスクトップへ出力
```
ONScripter_Multi_Converter.exe -cl -i "C:/Program Files (x86)/07th_Expansion/Umineko8" -o "C:/Users/佐藤裕也/Desktop"
```


#### CLIモード有効、個別設定有効、変換ハードはBrainで、インストール済みの「はるのあしおと(非NScripter作品)」をEドライブのルート直下へ出力
```
ONScripter_Multi_Converter.exe -cl -t minori_haruoto -hw Brain -i "C:/Program Files (x86)/minori/はるのあしおと" -o "E:/"
```

