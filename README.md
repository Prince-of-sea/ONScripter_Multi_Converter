# ONScripter_Multi_Converter
## ツールについて
 特定の端末のONScripter向けに~~今更~~制作された総合変換ツールです。<br>
 一応[C&D; Tools Win GUI](https://web.archive.org/web/20170419120050fw_/http://www.geocities.jp/stm_torm/ons/tool.html)の後継を目指し作りました<br>


## 動作環境
 対応OS等の細かい検証は特に行っていません<br>
 多分windows10以降なら普通に動くと思います<br>
 <br>
 [制作/検証に使用した作者のPC環境]<br>
 PCスペック:<br>
 [![CPU-Z](https://valid.x86.fr/cache/banner/izbfap-2.png)](https://valid.x86.fr/izbfap)<br>
 FFmpeg-version:version 7.1-full_build<br>
 Python-version:Python 3.11.9<br>


## 動作に必要なもの
 - "ONScripter_Multi_Converter" exe本体 [[DL]](https://github.com/Prince-of-sea/ONScripter_Multi_Converter/releases/latest)
 - smjpeg_encode.exe(すとーむ様作成) [[DL]](http://web.archive.org/web/20130203074100/http://www.geocities.jp/stm_torm/ons/smjpeg4.zip)
 - nsaed.exe(すとーむ様作成) [[DL]](https://web.archive.org/web/20130328141650/http://www.geocities.jp/stm_torm/nsaed2.zip)
 - GARBro.Console(게지네様作成) [[DL]](https://drive.google.com/file/d/1gH9nNRxaz8GexN0B1hWyUc3o692bkWXX/view)
 - FFmpeg / FFprobe [[DL]](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z)
 - NScripterで制作された、またはONScripter用に変換されたゲーム


## 使い方
### 変換前準備
 DLしたファイルをそれぞれの場所に展開/移動し、<br>
 最終的にファイルを以下のような配置にして準備完了です<br>
 (ディレクトリの場所は問いません)
```
[パスの通ってるディレクトリ]
   ffmpeg.exe
   ffprobe.exe


[適当な名前のツール用ディレクトリ]
│  ONScripter_Multi_Converter.exe
│  
└─tools
    │  nsaed.exe
    │  smjpeg_encode.exe
    │
    └─Garbro_console
        │  GARbro.Console.exe
        │  {その他大量のファイル}
        │
        └─  {その他いくつかのディレクトリ}
```

### ツールの設定
 ![インターフェース](./md_ui_full.png)<br>
 ※画像は古いバージョンや開発中バージョンの場合があります<br>
 
 [こちらに詳しく書いてあります](./README_setting.md)<br>
~~よくわからないならハード変更だけしてあと入力/出力指定してconvert押せばいいと思います~~


## 注意事項など
### 仕様
 - 本ツールは以下のバージョンのONScripterで動作させることを想定して作っています
    - PSP: onscripter-20110111_psp
    - PSVITA: ONScripter-jh-PSVita (yuri) v0.5.1.3 ※日本語で確認

 - PSP利用時、対応しているゲームの解像度は基本的には4種類のみです<br>
 以下の解像度以外は変換が行えないと思ってください<br>
 ※一応v2.0.0以降は横解像度が640または800から+-10の場合に強制変換できるようになっています<br>
    - 800x600
    - 640x480
    - 400x300 ~~←正直怪しい~~
    - 320x240 ~~←これも正直怪しい~~

 - 解像度が対応しているゲーム作品であっても、<br>
 そのソフトが正常に動作するとは限りません<br>
 (ONSの仕様上、DLLとかlua依存の作品は無理)<br>

 - 動画を連番に指定すると進捗バーが89%で長時間止まることがあります<br>
 そのまま待っていれば終わると思います<br>

 - 本ツールは日本語専用です<br>

### CD-DAを使っているソフトについて
ONScripter側の[CD audio 演奏の振り替え機能](https://onscripter.osdn.jp/onscripter.html#cd-audio-mapping)を利用するため、<br>
先に吸い出した音源(wav)を入力先に用意しておいてください<br>
oggなどへの変換は本ツールが行うため事前の変換は不要です<br>

### 既知の不具合
 - avi、mpegplay、rnd2など一部関数を元々defsubで上書きしていた場合、本ツールの機能と競合する
 - nsa/sar/ns2アーカイブの外にあるnbzは処理不能

### お約束
 - 本ツールの使用において生じた問題や不利益などについて、<br>
 製作者は一切その責任を負わないものとします<br>
 また、それらの問題を他のツールの製作者様や<br>
 メーカー/サークル様に問い合わせるのは**絶対にやめてください**<br>

### 最後に
~~...今更PSP/VITAで変換してまでノベルゲームやるやついる？~~<br>