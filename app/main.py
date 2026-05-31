"""エントリポイント。GUI を起動する。

開発実行:  python -m app.main   （プロジェクトルートで）
同梱実行:  ScrollBot.exe / ScrollBot.app をダブルクリック
"""
from __future__ import annotations

import sys


def _selftest() -> int:
    """GUIなしで1回実行して結果を出力（パッケージ版の動作確認用）。

    保存済みセッション(profiles/<profile>/storage_state.json)があればログインを
    スキップして最下部までスクロールする。終了コード0=成功。
    """
    try:
        from app.config_loader import load_config
        from app.credentials import load_credentials
        from app.core import ScrollBot
        from app.logger import Logger
    except ImportError:
        from config_loader import load_config
        from credentials import load_credentials
        from core import ScrollBot
        from logger import Logger

    log = Logger(status_cb=lambda m: print("STATUS:", m))
    try:
        cfg = load_config()
        cfg["browser"]["headless"] = True  # 自己診断はヘッドレス
        # --tabs N でタブ数を指定（省略時は config の既定）
        if "--tabs" in sys.argv:
            try:
                cfg["tabs"] = max(1, int(sys.argv[sys.argv.index("--tabs") + 1]))
            except Exception:
                pass
        bot = ScrollBot(cfg, load_credentials(), log)
        bot.run()
        print("SELFTEST: OK")
        return 0
    except Exception as e:  # noqa
        print("SELFTEST: FAILED ->", repr(e))
        return 1


def _print_paths() -> int:
    """解決されたデータ保存先などを表示（書き込み可否の確認用）。"""
    try:
        from app import paths, credentials
    except ImportError:
        import paths, credentials  # type: ignore
    print("frozen     :", paths.is_frozen())
    print("data_dir   :", paths.data_dir())
    print("env_path   :", paths.env_path())
    print("profiles   :", paths.profiles_dir())
    print("logs       :", paths.logs_dir())
    print("browser_dir:", paths.browser_dir(), "(exists:", paths.browser_dir().exists(), ")")
    # 書き込みテスト
    try:
        t = paths.data_dir() / ".write_test"
        t.write_text("ok", encoding="utf-8")
        t.unlink()
        print("writable   : True")
    except Exception as e:
        print("writable   : False ->", e)
    print("has_credentials:", credentials.has_credentials())
    return 0


def _set_cred(argv) -> int:
    """CLIから認証情報を保存（自動化/検証用）。--set-cred <ID> <PW>"""
    try:
        from app import credentials
    except ImportError:
        import credentials  # type: ignore
    i = argv.index("--set-cred")
    try:
        login_id, password = argv[i + 1], argv[i + 2]
    except IndexError:
        print("usage: --set-cred <ID> <PASSWORD>")
        return 1
    credentials.save_credentials(login_id, password)
    print("saved. has_credentials:", credentials.has_credentials())
    return 0


def main() -> None:
    if "--paths" in sys.argv:
        sys.exit(_print_paths())
    if "--set-cred" in sys.argv:
        sys.exit(_set_cred(sys.argv))
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    # PyInstaller 同梱/開発実行どちらでも import 可能にする
    try:
        from app.gui import launch  # 開発実行(python -m app.main)
    except ImportError:
        from gui import launch  # 同梱時のフォールバック
    launch()


if __name__ == "__main__":
    sys.exit(main())
