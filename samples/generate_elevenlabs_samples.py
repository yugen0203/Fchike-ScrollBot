#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ElevenLabs 音声サンプル生成スクリプト（要件定義 フェーズ0）
本番に近い文言（要件定義 7.1〜7.4）で受付AIの音声サンプルを生成する。

使い方:
  export ELEVENLABS_API_KEY=xxxx
  python3 samples/generate_elevenlabs_samples.py

出力: samples/out/ に mp3 を保存
"""
import os
import sys
import json
import pathlib
import urllib.request
import urllib.error

API_KEY = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("XI_API_KEY")
# 日本語対応・低遅延なら eleven_turbo_v2_5 / eleven_flash_v2_5、品質重視なら eleven_multilingual_v2
MODEL_ID = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
# 任意で上書き可。未指定なら voices 一覧から日本語向け女性ボイスを自動選択。
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID")

OUT_DIR = pathlib.Path(__file__).parent / "out"

# 本番に近い受付文言（要件定義 7章より）
LINES = {
    "01_録音告知": "株式会社Rion Lab Japanです。こちらのお電話は品質向上のため録音させていただきます。",
    "02_受付開始": "はい。株式会社Rion Lab Japanでございます。ご予約をお伺いできますか？",
    "03_折り返し案内": "承知しました。あいにく現在担当者が不在ですので、折り返しご連絡させていただきます。お電話番号とお名前を頂戴できますでしょうか？",
    "04_復唱確認": "ありがとうございます。山田様、お電話番号は090-1234-5678、ご用件は来週のお打ち合わせ日程のご相談で承りました。担当者より折り返しご連絡いたします。本日はお電話ありがとうございました。",
}


def http_get(url):
    req = urllib.request.Request(url, headers={"xi-api-key": API_KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def pick_voice():
    """日本語を含む multilingual 想定で、女性ボイスを優先選択。"""
    data = http_get("https://api.elevenlabs.io/v1/voices")
    voices = data.get("voices", [])
    if not voices:
        raise SystemExit("利用可能なボイスが見つかりませんでした。")
    # 女性 → ナレーション/落ち着いた声を優先
    def score(v):
        labels = v.get("labels", {}) or {}
        s = 0
        if labels.get("gender") == "female":
            s += 2
        if labels.get("use_case") in ("narration", "conversational", "customer_support"):
            s += 1
        return s
    voices.sort(key=score, reverse=True)
    chosen = voices[0]
    print(f"[voice] 自動選択: {chosen.get('name')} ({chosen.get('voice_id')}) labels={chosen.get('labels')}")
    return chosen["voice_id"]


def synth(voice_id, text, out_path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = json.dumps({
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        out_path.write_bytes(r.read())
    print(f"[ok] {out_path}  ({out_path.stat().st_size} bytes)")


def main():
    if not API_KEY:
        sys.exit("ERROR: ELEVENLABS_API_KEY が未設定です。export してから再実行してください。")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    voice_id = VOICE_ID or pick_voice()
    print(f"[model] {MODEL_ID}  [voice] {voice_id}")
    for name, text in LINES.items():
        try:
            synth(voice_id, text, OUT_DIR / f"{name}.mp3")
        except urllib.error.HTTPError as e:
            print(f"[error] {name}: HTTP {e.code} {e.read().decode('utf-8', 'ignore')}")
        except Exception as e:
            print(f"[error] {name}: {e}")


if __name__ == "__main__":
    main()
