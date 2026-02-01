# Steer-RC 🛠️

**Windows 側でジョイスティック入力を読み取り、UDP で Raspberry Pi に送信して車両を制御するプロジェクト**です。

---

## 🔎 概要

- `Win.py` — Windows 上でジョイスティックを読み取り、UDP で制御データを送るコンソール向け送信クライアントです。
- `raspi.py` — Raspberry Pi 側の受信プログラム。`adafruit_pca9685` を使ってサーボ/ESC を制御します。
- ビルド・配布用のスクリプト（`build_win_exe.bat`, `build_win_exe.ps1`, `build_windows.ps1`）と PyInstaller の `win.spec` を含みます。

> 以前の README にあった GUI（`Win_gui.py`）はこのリポジトリには含まれていません。GUI の静的プレビューは `ui_preview.html` を参照してください。

---

## ✅ 必要な依存関係

- 共通（Raspberry Pi 向け含む）: see `req.txt`
  - adafruit-circuitpython-pca9685
  - adafruit-circuitpython-motor
  - RPi.GPIO (Linux のみ)
  - websockets
  - pygame
  - PySimpleGUI
  - pyinstaller
  - pyvirtualdisplay
  - Pillow
  - Flask
  - flask-socketio

- Windows 実行/ビルド用: `req_win.txt`（例: `pygame`, `pyinstaller`）

インストール例:
```bash
python -m pip install -r req.txt
# Windows でビルド環境を用意する場合:
python -m pip install -r req_win.txt
```

---

## ⚙️ 使い方（簡単）

### Windows (送信側)
- コンソール版の起動:
```bash
python Win.py [--ip <RPI_IP>] [--port <PORT>] [--no-interactive]
```
- 重要なオプション:
  - `--ip` : 送信先 Raspberry Pi の IP（省略時は `192.168.11.2`）
  - `--port` : UDP ポート（省略時は `5005`）
  - `--no-interactive` : 対話的プロンプトをスキップしてデフォルトを使用します

- ボタン操作・挙動:
  - ステアリング: アナログ軸（axis 0）
  - スロットル: axis 1（負方向がアクセル）
  - ブレーキ: axis 2
  - スロットル調整ボタン（例: paddles）でレンジを上下できます（`Win.py` 内の定数を参照）
  - 方向切替用ボタンで前進/後退を切り替えます

### Raspberry Pi (受信側)
```bash
python raspi.py
```
- `raspi.py` は UDP を受け取り、`adafruit_pca9685` を介してサーボと ESC を制御します。I2C (SCL/SDA) と ESC/サーボ の配線を正しく行ってから起動してください。
- 注意: `adafruit-circuitpython-*` 系は Raspberry Pi 環境での実行を想定しています。

---

## 🔧 ビルド (.exe) とリリース

- Windows 上でローカルビルドを行うには `build_win_exe.ps1`（PowerShell）または `build_win_exe.bat` を使用します。
- PyInstaller を使った onefile ビルド結果は `dist\` に出力されます。
- CI（GitHub Actions）で Windows ランナーを使って自動ビルドするワークフローがあればアーティファクトをダウンロードできます（`BUILD_EXE.md` を参照）。

---

## 🩺 トラブルシューティング

- ジョイスティックが検出されない場合: 接続/ドライバ/他アプリの排他を確認してください。
- Raspberry Pi で I2C デバイスが見えない場合: `i2cdetect` や配線を確認し、`RPi.GPIO` のインストールと有効化を行ってください。
- ビルド時に pygame のネイティブモジュールが落ちる場合は Windows 実機でビルドしてください。

---

## 📁 リポジトリ内の主なファイル

- `Win.py` — 送信クライアント（コンソール）
- `raspi.py` — 受信・モータ/サーボ制御
- `req.txt`, `req_win.txt` — 依存パッケージ
- `build_win_exe.bat`, `build_win_exe.ps1`, `build_windows.ps1` — ビルド補助スクリプト
- `win.spec` — PyInstaller spec
- `ui_preview.html` — GUI の静的プレビュー（GUI 本体は未収録）
- `BUILD_EXE.md`, `memo.txt` — ドキュメント/メモ

---

## 貢献・問い合わせ

プルリク歓迎です。Issue を立ててください。

---

*更新日時*: 2026-02-01


