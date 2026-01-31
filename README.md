# Steer-RC - Windows controller helper (GUI)

このリポジトリには Windows 側でジョイスティック入力を読み取り、UDP で Raspberry Pi に送信するツールが含まれます。

## 実行方法 ✅

1. Python 環境を用意して依存パッケージをインストールします:

   ```bash
   pip install -r req.txt
   ```

2. GUI を起動します (Windows で実行することを想定しています):

   ```bash
   python Win_gui.py
   ```

   - スタート前に IP/ポートやレンジ、ボタン割り当てを GUI 上で調整できます。
   - エラーが発生すると画面にポップアップとログが表示されます。

   ※ ヘッドレス/テスト環境では GUI を使わずに実行することもできます:

   ```bash
   python Win_gui.py --nogui
   ```
   - `--nogui` モードではコンソールにログが出力され、ジョイスティックが接続されていれば同様にデータ送信を行います。

   - ヘッドレス環境で GUI の見た目だけ確認したいときは静的プレビューを出力できます（ファイル: `ui_preview.html`）:

   ```bash
   python Win_gui.py --preview
   ```

   - また、仮想ディスプレイ (Xvfb) と Pillow が利用できる場合は GUI を起動してスクリーンショットを保存できます:

   ```bash
   python Win_gui.py --screenshot
   ```
   - 生成されるファイル: `ui_screenshot.png`（成功すれば出力されますが、環境によっては追加パッケージが必要です）

## .exe にビルドする方法 (PyInstaller) 🔧

- ローカルで Windows 実機からビルドする場合 (PowerShell):

  ```powershell
  .\build_windows.ps1
  ```

  または手動で:

  ```powershell
  python -m pip install --upgrade pip
  python -m pip install -r req.txt
  python -m pip install pyinstaller
  pyinstaller --onefile --windowed --name SteerRC Win_gui.py
  ```

- 生成物は `dist\SteerRC.exe` になります。

- GitHub Actions を使って自動ビルドすることもできます（Windows runner でビルドしてアーティファクトをダウンロードできます）。

  - ワークフロー: `.github/workflows/build-windows.yml` を用意済みです。`Actions` → `Build Windows exe` から手動実行 (workflow_dispatch) するか、main ブランチへの push によって自動でビルドされます。
  - ビルド後、`SteerRC-windows-exe` アーティファクトをダウンロードして実行してください。

- 注意: `pygame` のネイティブ部分などは Windows の環境に依存するため、**ビルドは Windows 環境で行ってください**（GitHub Actions の Windows runner も利用可能です）。

## 変更の永続化

- GUI で保存ボタンを押すと `controller_config.json` に設定が保存されます。

## トラブルシューティング ⚠️

- ジョイスティックが見つからない場合: 接続とドライバ、他のアプリでの排他使用を確認してください。
- エラーは GUI のログ領域とポップアップで確認できます。
- PySimpleGUI のインストールに関する警告やテーマ API が見つからないエラーが出る場合は、以下の手順で再インストールしてください（特に該当メッセージが出る環境向け）:

  ```bash
  python -m pip uninstall PySimpleGUI
  python -m pip cache purge
  python -m pip install --upgrade --extra-index-url https://PySimpleGUI.net/install PySimpleGUI
  ```
  または明示的に再インストールする場合:
  ```bash
  python -m pip install --force-reinstall --extra-index-url https://PySimpleGUI.net/install PySimpleGUI
  ```

  ※ macOS / Linux の場合は `python3 -m pip` を使用してください。

- Headless（表示のない Linux）環境で GUI を表示したい場合

  - 推奨方法（システム側に Xvfb を入れて pyvirtualdisplay を使う）:
    ```bash
    sudo apt-get update && sudo apt-get install -y xvfb
    python3 -m pip install pyvirtualdisplay
    python3 Win_gui.py
    ```
  - あるいは単発で xvfb を使って起動する:
    ```bash
    xvfb-run python3 Win_gui.py
    ```
  - これが無い場合は `Win_gui.py` は自動でヘッドレス（--nogui と同等）にフォールバックしてコンソールログのみを出力します。

---

