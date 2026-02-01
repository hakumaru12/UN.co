# PyInstaller で `Win.py` を exe にする手順 ✅

概要
- このリポジトリには `Win.py`（ゲームパッド→UDP送信）が含まれています。
- `pyinstaller` を使って、実行時にコンソールが表示される exe を作るためのスクリプトと spec を用意しました。

用意したファイル
- `win.spec` - pygame のサブモジュールとデータを収集するための spec
- `build_win_exe.sh` - Unix 系での簡易ビルドスクリプト
- `build_win_exe.bat` - Windows 上での簡易ビルドバッチ

重要なポイント ⚠️
- PyInstaller は実行するプラットフォーム向けにバイナリを作ります。Windows の .exe を作るには Windows 上でビルドする必要があります（または Wine / cross-compilation 環境を使う）。
- コンソールを必ず表示したい場合は `--console` を付けるか、`spec` の `EXE(..., console=True)` を使ってください。
- pygame の資産が抜けることがあるので、その場合は `pyinstaller win.spec` を試してください（spec は pygame のデータを collect します）。

ビルド手順（Windows の場合）
1. Python と PyInstaller をインストールします:
   pip install pyinstaller
2. コマンドプロンプトでこのリポジトリのルートに移動し、次を実行:
   build_win_exe.bat
3. 成功すると `dist\Win.exe` が生成されます。ダブルクリックまたはコマンドプロンプトで実行するとコンソールが表示されます。

補足（デバッグ）
- 実行時に pygame がコントローラを見つけられないと例外を出します。exe をコマンドプロンプトから起動するとログが見やすいです。

CI（GitHub Actions）でのビルド
- このリポジトリには Windows ランナーで `.exe` を自動ビルドする workflow が追加されています: `.github/workflows/build-windows.yml`
- ワークフローは `push`（`main`）と手動トリガ（`workflow_dispatch`）で動作し、`Win_gui`（GUI版）と `Win`（コンソール版）をビルドして成果物（artifact）としてアップロードします。
- ワークフローを手動で実行するには GitHub の Actions タブで `Build Windows exe` ワークフローを選び `Run workflow` を押してください。ビルド後に `Artifacts` から `Win-windows-exe` をダウンロードできます。

ローカル Windows でのビルド補助
- `build_win_exe.bat`（既存）または `build_win_exe.ps1`（PowerShell 補助）を使って手元の Windows でビルドできます。`build_win_exe.ps1` は依存のインストールと spec ベースのフォールバックを含みます。

---
もう手元で試してほしい点があれば教えてください（例: アイコン追加、onefile/onedir の変更、UPX の有効化など）。