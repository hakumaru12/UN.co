# Steer-RC 🛠️

**Windows 側でジョイスティック入力を読み取り、UDP で Raspberry Pi に送信して車両を制御するプロジェクト**です。

---

## 🔎 概要

このプロジェクトはRC車両を **Logitech GT Force Pro** ジョイスティックで制御するシステムです：

- **`Win.py`** — Windows 上でジョイスティスティック（GT Force Pro）を読み取り、UDP で制御データを Raspberry Pi に送信するコンソール向け送信クライアントです。ステアリング、スロットル、ブレーキのアナログ入力と、方向切り替えボタンをサポートしています。
- **`raspi.py`** — Raspberry Pi 側の受信プログラム。`adafruit_pca9685` を使ってサーボ/ESC を制御します。I2C 経由で PCA9685 PWM コントローラに接続します。
- **`Boot.sh`** — Raspberry Pi 起動時に Wi-Fi 接続の確認とビデオストリーミングを自動開始するスクリプトです。GStreamer を使って映像を UDP で送信します。
- ビルド・配布用のスクリプト（`build_win_exe.bat`, `build_win_exe.sh`）と PyInstaller で `.exe` を生成できます。

> 以前の README にあった GUI（`Win_gui.py`）はこのリポジトリには含まれていません。

---

## ✅ 必要な依存関係

### 共通（全環境）
`req.txt` に記載されているパッケージ：
```
adafruit-circuitpython-pca9685
adafruit-circuitpython-motor
RPi.GPIO
websockets
```

### Raspberry Pi 側（実行時）

Python パッケージ:
```bash
pip install -r req.txt
```

システムパッケージ（GStreamer、ビデオストリーミング用）:
```bash
sudo apt update
sudo apt upgrade
sudo apt -y install \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav \
  gstreamer1.0-gl \
  gstreamer1.0-gtk3 \
  gstreamer1.0-pulseaudio \
  gstreamer1.0-alsa \
  tmux
```

詳細は [req_raspi.txt](req_raspi.txt) を参照してください。

### Windows 側（送信クライアント用）
`req_win.txt` に記載：
```
pygame==2.6.1
```

全基本パッケージはコマンドラインで以下のようにインストール：
```bash
python -m pip install pygame==2.6.1 pyinstaller
```

### PyInstaller ビルド用
```bash
pip install pyinstaller
```

---

## ⚙️ 使い方（簡単）

### Windows (送信側)

#### コンソール版の起動:
```bash
python Win.py [--ip <RPI_IP>] [--port <PORT>] [--no-interactive]
```

#### オプション:
- `--ip <IP>` : 送信先 Raspberry Pi の IP（省略時は `192.168.11.2`）
- `--port <PORT>` : UDP ポート（省略時は `5005`）
- `--no-interactive` : 対話的プロンプトをスキップしてデフォルト値を使用します

#### ジョイスティック操作:
- **ステアリング** : アナログ軸 0（左右）- ±23° 範囲にマップされます
- **スロットル** : アナログ軸 1（負方向で奥に引く）- スロットルペダル
- **ブレーキ** : アナログ軸 2（奥に引く）- 即座に停止
- **スロットル調整** :
  - ボタン 4（右パドル）: スロットル上限を 5% ずつ増加（最大 100%）
  - ボタン 5（左パドル）: スロットル上限を 5% ずつ減少（最小 30%）
- **方向切り替え** : ボタン 19（中央ボタン）で前進/後退を切り替え
  - 後退時は「ダブルバック」機能が自動的にESCを初期化します

#### コントローラー未接続時:
プログラムは接続まで待機します。コントローラを接続してから Enter キーを押すか、`q` を入力して終了できます。

### Raspberry Pi (受信側)

#### 起動方法:
```bash
python raspi.py
```

#### 動作:
- UDP ポート 5005 でデータを受信
- I2C 经由で PCA9685 PWM コントローラに接続
- チャンネル 0: サーボモータ（ステアリング制御）
- チャンネル 1: ESC（電子スピードコントローラ - スロットル制御）

#### 初期化:
起動時に ESC の初期化処理を行います。この時点でプロペラは回転しないよう設計されています。

#### 配線確認:
- I2C: SCL（pin 5）, SDA（pin 3）に接続
- サーボ: PCA9685 チャンネル 0
- ESC: PCA9685 チャンネル 1

#### ビデオストリーミング (Boot.sh 利用):
Raspberry Pi 起動時に自動的にビデオストリーミングを開始する場合は `Boot.sh` を使用：
```bash
sudo chmod +x Boot.sh
./Boot.sh
```

このスクリプトは以下を実行します：
1. Wi-Fi に接続するまで待機（デフォルト: `BF-HSKK-2.4G`）
2. IP アドレスを表示
3. GStreamer でビデオキャプチャ（`/dev/video0`）を開始
4. H.264 エンコーディングして UDP で映像を送信（`192.168.11.2:5000`）
5. `raspi.py` を起動（RC 制御）

**注:** SSID、IP、ポート等は [Boot.sh](Boot.sh) 内で変更できます。

---

## 🔧 ビルド (.exe) とリリース

### Windows でのローカルビルド

PyInstaller を使って Windows 実行ファイル（`.exe`）を生成します。

#### 簡単ビルド（bash 環境）:
```bash
./build_win_exe.sh
```

#### Windows コマンドプロンプト:
```bat
build_win_exe.bat
```

#### ビルド詳細:
- **コマンド例**: `pyinstaller --clean --noconfirm --onefile --name Win --console Win.py`
- **結果**: `dist/Win.exe` が生成されます
- **構成**: ワンファイル化、コンソール表示モード

#### 注意事項:
- PyInstaller はターゲットプラットフォーム向けのネイティブ実行ファイルを生成するため、**Windows 上でビルドする必要があります**
- Linux/macOS でビルドした場合は、結果は `dist/Win` となります
- pygame など一部のライブラリはネイティブコンポーネントを含むため、ターゲット環境でのビルドが推奨されます

---

## 🩺 トラブルシューティング

### Windows (Win.py)

| 問題 | 解決策 |
|------|--------|
| ジョイスティック（GT Force Pro）が検出されない | コントローラを再接続、ドライバを確認、他のアプリがコントローラを占有していないか確認 |
| `pygame` エラー | `python -m pip install pygame==2.6.1` で再インストール |
| IP/ポートが違う場合 | `--ip` と `--port` オプションで指定、または対話プロンプトで設定 |
| UDP を受け取れない | ファイアウォール設定を確認、Raspberry Pi が起動しているか確認 |

### Raspberry Pi (raspi.py)

| 問題 | 解決策 |
|------|--------|
| I2C デバイスが見つからない | `i2cdetect -y 1` で I2C デバイスを確認、PCA9685 の配線をチェック（SCL/SDA） |
| `adafruit-circuitpython-pca9685` インポートエラー | `pip install --break-system-packages adafruit-circuitpython-pca9685` でインストール |
| RPi.GPIO エラー | `sudo apt install python3-rpi.gpio` + `pip install --break-system-packages RPi.GPIO` |
| サーボ/ESC が動作しない | PCA9685 の電源供給を確認、PWM 信号の周波数（50Hz）を確認 |

### GStreamer ビデオストリーミング (Boot.sh)

| 問題 | 解決策 |
|------|--------|
| `gst-launch-1.0` コマンドが見つからない | `sudo apt install gstreamer1.0-tools` でインストール |
| Wi-Fi に接続できない | `Boot.sh` の `TARGET_SSID` と `TARGET_IP` を確認・修正 |
| ビデオデバイス `/dev/video0` がない | `ls /dev/video*` で利用可能なデバイスを確認 |
| UDP ストリーミングが到達しない | ファイアウォール設定、IP アドレスが正しいか確認 |

### PyInstaller ビルド失敗

| 問題 | 解決策 |
|------|--------|
| pygame ネイティブモジュールエラー | **Windows 上でビルドしてください**。pygame は C 拡張を含みます |
| `dist/` フォルダが空 | ビルドログを確認、`build/` ディレクトリを削除して再ビルド |
| `.exe` が実行時に落ちる | antivirus ソフトの除外設定、UACの確認 |

---

## 📁 リポジトリ内の主なファイル

### プログラムコード
- **`Win.py`** — Windows 送信クライアント（コンソール版）。Logitech GT Force Pro ジョイスティック入力を読み取り、UDP で Raspberry Pi に制御データを送信します
- **`raspi.py`** — Raspberry Pi 受信プログラム。UDP データを受け取り、I2C 経由で PCA9685 コントローラを制御し、サーボとESCを動作させます（107行）

### ビルド・スタートアップ
- **`Boot.sh`** — Raspberry Pi 起動スクリプト。Wi-Fi 接続確認、GStreamer ビデオストリーミング起動、`raspi.py` の自動実行を行います
- **`build_win_exe.bat`** — Windows コマンドプロンプト用ビルドスクリプト。PyInstaller で `.exe` を生成します
- **`build_win_exe.sh`** — Linux/macOS/Git Bash 用ビルドスクリプト

### 依存関係ファイル
- **`req.txt`** — Python 基本パッケージリスト
  - adafruit-circuitpython-pca9685
  - adafruit-circuitpython-motor
  - RPi.GPIO
  - websockets
- **`req_win.txt`** — Windows 制御用パッケージ（pygame 2.6.1）
- **`req_raspi.txt`** — Raspberry Pi セットアップ用コマンド集（システムパッケージと pip パッケージのインストール手順）

### ドキュメント・メモ
- **`README.md`** — このファイル。プロジェクト概要、セットアップ、使い方を記載
- **`memo.txt`** — 開発時のメモ。セットアップコマンドや GStreamer 設定メモ

### ビルド成果物
- **`build/`** — PyInstaller により生成されるビルド中間ファイルディレクトリ
  - `build/Win/` — Windows ビルド中間ファイル（`.toc`、`.pyz` など）
  - ビルド後は `dist/` に最終実行ファイルが出力されます

---

## 📝 技術仕様

### UDP通信フォーマット

Windows → Raspberry Pi へ送信されるデータ：
```python
struct.pack('ffi', steering_angle, throttle_value, direction)
```

| フィールド | 型 | 範囲 | 説明 |
|-----------|-----|------|--------|
| `steering_angle` | float | -23 ～ +23 | ステアリング角度（度） |
| `throttle_value` | float | 0 ～ 100 | スロットル値（パーセンテージ） |
| `direction` | int | 1 / -1 | 前進（1）/ 後退（-1） |

### 周期
- **送信周期**: 20ms（50Hz）
- **ESC PWM周波数**: 50Hz
- **サーボのニュートラル位置**: 0° / 90°（全振幅で -23°～+23°）

### ESC/ スロットル制御
- **ニュートラル**: 7.5%（0.075 duty cycle）
- **前進**: 7.5% + (スロットル% / 100) × 2.5%
- **後退**: 7.5% - (スロットル% / 100) × 2.5%

---

## 🔐 セキュリティ・注意事項

- このマシンは **ローカルネットワーク内での使用を想定**しています
- UDP は暗号化されていないため、本番環境では適切なセキュリティ対策を追加してください
- RC 車両では **誤操作で事故が発生する可能性** があります。必ずテスト環境で十分な動作確認を行いましょう
- 後退機能は「ダブルバック」によるESC初期化が自動的に行われます。急激な後退は避けてください

---

## 📄 ライセンス

This project is for educational and hobbyist purposes. Please follow local regulations for RC vehicle operation.

---

## 🙏 貢献・問い合わせ

機能提案やバグ報告は Issue/PR でお願いします。プルリクエストも歓迎です。

---

*更新日時*: 2026-02-12


