"""出品フロー本体（ListBot 用）。

実DOM捕捉（2026-05-31, Fチケ）で判明した実フローに対応:

  シーズンページ(最下部までスクロール)
    → 対象日付のアコーディオン(button.UITicketAccordion_Button)を開く
    → 未出品席の「出品する」(UIAppButton _small _none)を押す → 出品登録ページ
  出品登録ページは【1ページで順次展開】する:
    STEP1: 各座席をチェック(button.UIResaleTicketCheckBox_Check) →
           価格入力(input.UIPriceEditor_Right_Input)に最高額を入れ Tab で確定(blur)
    → 「次へ」(#PageResaleRegisterTranslateBtn) で STEP2 が出現
    STEP2: バラ売り可/不可(label.UIRadioButton, name=isPackage)を選択
    → 「次へ」で STEP3(確認)が出現。ボタンのラベルが「出品する」(class _danger)に変化
    STEP3: 「出品する」(同じ #PageResaleRegisterTranslateBtn)で確定 → 出品完了

連番グルーピングは grouping.py、価格(最高額)解析は pricing.py を使用。
セレクタは config_listbot.yml の sites.<active>.listing から取得（ハードコードしない）。

⚠️ confirm_mode=True のとき STEP3 の最終「出品する」直前で停止する（誤出品防止・テスト用）。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .config_loader import active_site
from .core import LoginError
from .grouping import decide_bara_ok, describe_groups, group_seats
from .logger import Logger
from .pricing import max_price

# 「Sec.103 11列 5番」等から section/row/num を抽出
_SEAT_RE = re.compile(
    r"(?:Sec\.?\s*)?(?P<section>[0-9A-Za-z\-]+)?\s*"
    r"(?P<row>[0-9]+)\s*列\s*"
    r"(?P<num>[0-9]+)\s*番"
)


def parse_seat_label(label: str) -> Optional[Dict[str, Any]]:
    """座席ラベル文字列を {section,row,num,label} に解析する。失敗時 None。"""
    if not label:
        return None
    m = _SEAT_RE.search(label)
    if not m:
        return None
    return {
        "section": (m.group("section") or "").strip(),
        "row": m.group("row"),
        "num": int(m.group("num")),
        "label": label.strip(),
    }


class ListingResult:
    def __init__(self):
        self.listed_groups: int = 0
        self.skipped: List[str] = []
        self.stopped_for_confirm: bool = False
        self.errors: List[str] = []


class ListingBot:
    """1ページ(=1日付)分の出品を担当する。複数日付は呼び出し側でタブを分けて並行実行する。"""

    def __init__(self, cfg: Dict, log: Logger, cancel_check=None, scroll_fn=None):
        self.cfg = cfg
        self.log = log
        self.cancel_check = cancel_check or (lambda: False)
        # 残りグループの出品ページを開き直す際に最下部までスクロールする関数（任意）
        self.scroll_fn = scroll_fn
        self.site = active_site(cfg)
        self.s: Dict[str, Any] = self.site.get("listing") or {}
        self.listing_cfg = cfg.get("listing") or {}
        self.grouping_rule = cfg.get("grouping") or {}
        self.pause = int(self.listing_cfg.get("between_actions_ms", 400)) / 1000.0
        self.confirm_mode = bool(self.listing_cfg.get("confirm_mode", False))

    # ---- ヘルパ ---------------------------------------------------------
    def _sel(self, key: str, default: str = "") -> str:
        v = self.s.get(key) or default
        if not v:
            raise LoginError(f"出品セレクタ '{key}' が未設定です（config_listbot.yml）")
        return v

    def _wait(self, page):
        page.wait_for_timeout(int(self.pause * 1000))

    def _check_cancel(self):
        if self.cancel_check():
            raise LoginError("ユーザーにより中断されました")

    # ---- 試合カードを日付で探して出品ページへ ---------------------------
    def _game_item(self, page, month: int, day: int):
        item_sel = self._sel("game_item", "li.UITicketSliderPc_List_Item")
        date_str = f"{month}/{day}"
        loc = page.locator(item_sel, has_text=date_str)
        # has_text は部分一致。9/1 が 9/17 を誤マッチしないよう、日付Dayテキストで厳密確認
        n = loc.count()
        for i in range(n):
            it = loc.nth(i)
            try:
                day_text = it.locator(self._sel("game_date_text",
                                                ".UITicketAccordion_Button_Date_Day")).first.inner_text(timeout=1500)
            except Exception:
                day_text = ""
            if self._date_day_matches(day_text, month, day):
                return it
        return None

    @staticmethod
    def _date_day_matches(text: str, month: int, day: int) -> bool:
        t = (text or "").replace(" ", "").replace("\n", "")
        return t in (f"{month}/{day}", f"0{month}/{day}", f"{month}/0{day}", f"0{month}/0{day}")

    def open_listing_page_for_date(self, page, month: int, day: int) -> bool:
        """対象日のアコーディオンを開き「出品する」を押して出品登録ページへ。

        未出品席が無ければ False。
        """
        item = self._game_item(page, month, day)
        if item is None:
            self.log.warn(f"{month}/{day} の試合カードが見つかりません")
            return False
        item.scroll_into_view_if_needed()
        self._wait(page)
        # アコーディオンを開く（既に開いていても無害）
        try:
            item.locator(self._sel("accordion_button", "button.UITicketAccordion_Button")
                         ).first.click(timeout=5000)
        except Exception:
            pass
        page.wait_for_timeout(1200)

        name = self.s.get("list_button_name", "出品する")
        btn = item.get_by_role("button", name=name)
        if btn.count() == 0:
            self.log.info(f"{month}/{day} に未出品席（{name}）がありません → スキップ")
            return False
        self.log.status(f"{month}/{day} の出品ページを開きます（未出品 {btn.count()} 席）")
        btn.first.scroll_into_view_if_needed()
        btn.first.click(timeout=8000)
        page.wait_for_load_state("domcontentloaded")
        self._wait_listing_page(page)
        return True

    def _wait_listing_page(self, page):
        seat_sel = self._sel("seat_item", ".UIResaleTicketCheckBox.PageResaleRegister_Step_Ticket_Item")
        try:
            page.wait_for_selector(seat_sel, timeout=15000)
        except Exception:
            raise LoginError("出品登録ページ(STEP1)の表示を確認できませんでした")
        page.wait_for_timeout(800)

    # ---- STEP1: 座席の列挙 ---------------------------------------------
    def enumerate_seats(self, page) -> List[Dict[str, Any]]:
        seat_sel = self._sel("seat_item", ".UIResaleTicketCheckBox.PageResaleRegister_Step_Ticket_Item")
        name_sel = self._sel("seat_name", ".UISeatPrice_Name")
        rows = page.locator(seat_sel)
        seats: List[Dict[str, Any]] = []
        for i in range(rows.count()):
            row = rows.nth(i)
            try:
                label = row.locator(name_sel).first.inner_text(timeout=2000)
            except Exception:
                continue
            parsed = parse_seat_label(label)
            if not parsed:
                self.log.warn(f"座席ラベル解析失敗: {label!r}")
                continue
            parsed["row_index"] = i
            seats.append(parsed)
        self.log.info(f"出品ページの座席 {len(seats)} 件: "
                      + ", ".join(s["label"] for s in seats))
        return seats

    # ---- 1日付分の出品 --------------------------------------------------
    def list_date(self, page, month: int, day: int, result: ListingResult) -> None:
        if not self.open_listing_page_for_date(page, month, day):
            result.skipped.append(f"{month}/{day}(未出品席なし)")
            return
        seats = self.enumerate_seats(page)
        if not seats:
            result.skipped.append(f"{month}/{day}(座席解析不可)")
            return

        groups = group_seats(seats, self.grouping_rule)
        self.log.info(f"{month}/{day} グループ構成: {describe_groups(groups)}")

        for gi, group in enumerate(groups):
            self._check_cancel()
            self.log.status(f"{month}/{day} グループ {gi + 1}/{len(groups)} を出品中 "
                            f"（{','.join(str(s['num']) for s in group)}番）")
            try:
                stopped = self._list_one_group(page, group)
                if stopped:
                    result.stopped_for_confirm = True
                    self.log.info("確認モード: 最終「出品する」直前で停止")
                    return
                result.listed_groups += 1
            except LoginError:
                raise
            except Exception as e:
                msg = f"{month}/{day} グループ {gi + 1} 出品失敗: {e}"
                self.log.error(msg)
                result.errors.append(msg)
            # 次グループのため出品ページを開き直す（最後以外）
            if gi < len(groups) - 1:
                if not self._reopen(page, month, day):
                    self.log.warn(f"{month}/{day} 残りグループの出品ページを開けませんでした")
                    break

    def _reopen(self, page, month: int, day: int) -> bool:
        try:
            page.goto(self.site["start_url"], wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        page.wait_for_timeout(800)
        # 最下部まで（遅延読み込みで対象カードが見えるように）
        if self.scroll_fn:
            try:
                self.scroll_fn(page)
            except Exception:
                pass
        return self.open_listing_page_for_date(page, month, day)

    # ---- グループ1つ分の出品 -------------------------------------------
    def _list_one_group(self, page, group: List[Dict[str, Any]]) -> bool:
        """1グループを出品。confirm_mode のとき最終ボタン直前で True を返す。"""
        seat_sel = self._sel("seat_item")
        check_sel = self._sel("seat_check", "button.UIResaleTicketCheckBox_Check")
        active_cls = self.s.get("seat_check_active_class", "_checked")
        target_idx = {s["row_index"] for s in group}

        rows = page.locator(seat_sel)
        total = rows.count()

        # 1) 対象座席だけチェック
        for i in range(total):
            self._check_cancel()
            chk = rows.nth(i).locator(check_sel).first
            cls = chk.get_attribute("class") or ""
            checked = active_cls in cls
            want = i in target_idx
            if want != checked:
                chk.click(timeout=4000)
                page.wait_for_timeout(300)
        self._wait(page)

        # 2) 対象座席に最高額を入力 → Tab で確定(blur)
        for s in group:
            self._check_cancel()
            self._set_price_max(page, rows.nth(s["row_index"]), s)
        page.wait_for_timeout(400)

        # 3) STEP1 → 次へ（STEP2 出現）
        self._advance(page, expect_not_disabled=True)
        page.wait_for_timeout(1200)

        # 4) バラ売り 可/不可
        bara_ok = decide_bara_ok(group, self.grouping_rule)
        self._select_bara(page, bara_ok)
        self.log.info(f"出品方法: {'バラ売り可(単独)' if bara_ok else 'バラ売り不可(連番)'}")
        page.wait_for_timeout(800)

        # 5) STEP2 → 次へ（STEP3 確認出現・ボタンが「出品する」に変化）
        self._advance(page)
        page.wait_for_timeout(1500)

        # 6) 最終「出品する」
        if self.confirm_mode:
            self.log.warn("確認モード: 最終「出品する」は押しません。画面で確認し手動で押してください。")
            return True
        self._submit(page)
        self._wait_complete(page)
        return False

    def _set_price_max(self, page, row, seat: Dict[str, Any]):
        note_sel = self._sel("price_note", ".UIPriceEditor_Left_Note")
        input_sel = self._sel("price_input", "input.UIPriceEditor_Right_Input")
        # 価格範囲（チェック後に出現）から最高額
        pmax = None
        try:
            pmax = max_price(row.locator(note_sel).first.inner_text(timeout=3000))
        except Exception:
            pass
        if not pmax:
            raise LoginError(f"座席 {seat['label']} の価格範囲(最高額)を取得できません")
        inp = row.locator(input_sel).first
        inp.click(timeout=4000)
        inp.fill(str(pmax), timeout=4000)
        inp.press("Tab")  # blur で「¥6,900」に確定（次へ有効化の条件）
        page.wait_for_timeout(250)
        self.log.info(f"価格入力: {seat['label']} = ¥{pmax:,}（最高額）")

    def _advance(self, page, expect_not_disabled: bool = False):
        btn_sel = self._sel("advance_button", "#PageResaleRegisterTranslateBtn")
        btn = page.locator(btn_sel).first
        if expect_not_disabled:
            try:
                page.wait_for_function(
                    "sel => { const b=document.querySelector(sel); return b && !b.disabled; }",
                    arg=btn_sel, timeout=8000)
            except Exception:
                raise LoginError("「次へ」ボタンが有効になりません（価格入力/確定を確認）")
        btn.click(timeout=8000)

    def _select_bara(self, page, bara_ok: bool):
        text = (self.s.get("bara_ok_text", "バラ売り可") if bara_ok
                else self.s.get("bara_ng_text", "バラ売り不可"))
        loc = page.get_by_text(text, exact=True)
        if loc.count() == 0:
            # 1席のみ等でバラ売り選択が出ない場合はスキップ
            self.log.info(f"バラ売り選択肢『{text}』が見つからないためスキップ")
            return
        loc.first.click(timeout=6000)

    def _submit(self, page):
        btn_sel = self._sel("advance_button", "#PageResaleRegisterTranslateBtn")
        submit_text = self.s.get("submit_text", "出品する")
        btn = page.locator(btn_sel).first
        # ラベルが「出品する」になっていることを確認（STEP3）
        try:
            label = btn.inner_text(timeout=3000).strip()
        except Exception:
            label = ""
        if submit_text not in label:
            self.log.warn(f"最終ボタンのラベルが想定と異なります: {label!r}（続行）")
        btn.click(timeout=10000)
        self.log.status("最終「出品する」を実行")

    def _wait_complete(self, page):
        marker = self.s.get("complete_marker", "出品完了")
        try:
            page.get_by_text(marker, exact=False).first.wait_for(timeout=20000)
            self.log.info("出品完了を確認")
        except Exception:
            self.log.warn("出品完了マーカーを確認できませんでした（要目視確認）")
