"""エントリポイント（ListBot / 出品Bot）。

開発実行:  python -m listbot.main        （GUI）
診断:      python -m listbot.main --paths
認証保存:  python -m listbot.main --set-cred <ID> <PW>
DOM捕捉:   python -m listbot.main --capture            （シーズンページのHTML/スクショを保存）
           python -m listbot.main --capture --date 9/17 （その試合の出品ページまで開いて保存）
グルーピング確認: python -m listbot.main --group 5,6,7,8
"""
from __future__ import annotations

import sys


def _print_paths() -> int:
    from listbot import credentials, paths
    print("frozen     :", paths.is_frozen())
    print("data_dir   :", paths.data_dir())
    print("env_path   :", paths.env_path())
    print("config     :", paths.config_path())
    print("profiles   :", paths.profiles_dir())
    print("logs       :", paths.logs_dir())
    print("browser_dir:", paths.browser_dir(), "(exists:", paths.browser_dir().exists(), ")")
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
    from listbot import credentials
    i = argv.index("--set-cred")
    try:
        login_id, password = argv[i + 1], argv[i + 2]
    except IndexError:
        print("usage: --set-cred <ID> <PASSWORD>")
        return 1
    credentials.save_credentials(login_id, password)
    print("saved. has_credentials:", credentials.has_credentials())
    return 0


def _group_demo(argv) -> int:
    """連番グルーピングの確認: --group 5,6,7,8 [--mode max_size --max 2]"""
    from listbot.grouping import describe_groups, group_seats
    i = argv.index("--group")
    nums = [int(x) for x in argv[i + 1].split(",") if x.strip()]
    rule = {"mode": "together"}
    if "--mode" in argv:
        rule["mode"] = argv[argv.index("--mode") + 1]
    if "--max" in argv:
        rule["max_group_size"] = int(argv[argv.index("--max") + 1])
    if "--remainder" in argv:
        rule["remainder"] = argv[argv.index("--remainder") + 1]
    seats = [{"section": "103", "row": "11", "num": n} for n in nums]
    groups = group_seats(seats, rule)
    print(f"rule={rule}")
    print(f"seats={nums} -> {describe_groups(groups)}")
    return 0


def _capture(argv) -> int:
    """ログイン → スクロール → シーズンページのHTML/スクショを保存。
    --date 9/17 を付けるとその試合の出品ページ(STEP1)まで開いて保存（出品はしない）。
    """
    from listbot import credentials, paths
    from listbot.config_loader import active_site, load_config
    from listbot.core import Session
    from listbot.logger import Logger

    log = Logger(status_cb=lambda m: print("STATUS:", m))
    cfg = load_config()
    site = active_site(cfg)
    out = paths.data_dir() / "capture"
    out.mkdir(parents=True, exist_ok=True)

    sess = Session(cfg, credentials.load_credentials(), log)
    sess.open()
    try:
        page = sess.context.new_page()
        sess.ensure_login(page)
        sess.close_initial_blank_tabs()
        sess.scroll_to_bottom(page)

        (out / "season.html").write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(out / "season.png"), full_page=True)
        print("saved:", out / "season.html", "/", out / "season.png")

        if "--date" in argv:
            md = argv[argv.index("--date") + 1]
            mo, da = [int(x) for x in md.replace("月", "/").replace("日", "").split("/")]
            lsel = site.get("listing") or {}
            lb = lsel.get("list_button")
            print(f"出品ページを開きます（{mo}/{da}）。list_button={lb!r}")
            # game_card が未設定でも、テキスト一致で日付付近の出品ボタンを試す
            try:
                # 日付テキストの近くの「出品する」を探す簡易版
                page.get_by_text(f"{mo}/{da}").first.scroll_into_view_if_needed(timeout=5000)
            except Exception:
                pass
            if lb:
                try:
                    page.locator(lb).first.click(timeout=8000)
                    page.wait_for_timeout(2500)
                    (out / "listing_step1.html").write_text(page.content(), encoding="utf-8")
                    page.screenshot(path=str(out / "listing_step1.png"), full_page=True)
                    print("saved:", out / "listing_step1.html")
                except Exception as e:
                    print("出品ページ取得失敗（list_button要確認）:", e)
        print("CAPTURE: OK ->", out)
        return 0
    except Exception as e:
        print("CAPTURE: FAILED ->", repr(e))
        return 1
    finally:
        sess.close()


def main() -> int:
    if "--paths" in sys.argv:
        return _print_paths()
    if "--set-cred" in sys.argv:
        return _set_cred(sys.argv)
    if "--group" in sys.argv:
        return _group_demo(sys.argv)
    if "--capture" in sys.argv:
        return _capture(sys.argv)
    try:
        from listbot.gui import launch
    except ImportError:
        from gui import launch  # 同梱時フォールバック
    launch()
    return 0


if __name__ == "__main__":
    sys.exit(main())
