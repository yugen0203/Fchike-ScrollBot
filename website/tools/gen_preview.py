#!/usr/bin/env python3
"""曜日テーマのトップ画面を近似したプレビューPNGを生成（cairosvg使用）。
   実サイトの厳密な再現ではなく、配色・レイアウト・キービジュアルの確認用。"""
import os, cairosvg

OUT = "/tmp/preview"
os.makedirs(OUT, exist_ok=True)
JP = "IPAGothic, 'DejaVu Sans', sans-serif"

T = {
 "mon": dict(name="Monday", concept="Fresh Start", bg="#f6f9fe", surface="#ffffff",
             heading="#10243f", muted="#5a6675", primary="#1f6dff", soft="#e6efff",
             border="#e3eaf4", g0="#1f6dff", g1="#36c6ff", rad=8),
 "tue": dict(name="Tuesday", concept="Momentum", bg="#fffaf6", surface="#ffffff",
             heading="#3a1d10", muted="#7a6258", primary="#ff5a36", soft="#ffe7df",
             border="#f6e2d6", g0="#ff7a18", g1="#ff3d6e", rad=999),
 "wed": dict(name="Wednesday", concept="Flow", bg="#f3fbf8", surface="#ffffff",
             heading="#0c3a31", muted="#4c6b62", primary="#0fae8b", soft="#d6f4ec",
             border="#d6ece4", g0="#11b58c", g1="#7fe3c0", rad=24),
 "thu": dict(name="Thursday", concept="Trust", bg="#fbfaf6", surface="#ffffff",
             heading="#15233f", muted="#5d6470", primary="#b8893b", soft="#f3ead6",
             border="#e7e3d6", g0="#1b2c4d", g1="#b8893b", rad=2),
 "fri": dict(name="Friday (+ 土日)", concept="Spark", bg="#fbf7ff", surface="#ffffff",
             heading="#2a103f", muted="#665a78", primary="#8b2fe6", soft="#f0e3ff",
             border="#ebe0f7", g0="#7b2ff7", g1="#ff7eb3", rad=20),
}

def art(key):
    g = "url(#ga)"
    bodies = {
     "mon": f'<rect x="40" y="40" width="320" height="320" rx="10" fill="none" stroke="{g}" stroke-width="2" opacity=".5"/>'
            f'<rect x="70" y="70" width="120" height="120" rx="8" fill="{g}"/>'
            f'<rect x="210" y="70" width="120" height="120" rx="8" fill="{g}" opacity=".55"/>'
            f'<rect x="70" y="210" width="120" height="120" rx="8" fill="{g}" opacity=".35"/>'
            f'<circle cx="270" cy="270" r="60" fill="{g}"/>',
     "tue": f'<polygon points="60,340 200,60 240,80 100,360" fill="{g}"/>'
            f'<polygon points="160,340 300,60 340,80 200,360" fill="{g}" opacity=".55"/>'
            f'<circle cx="300" cy="120" r="44" fill="{g}" opacity=".8"/>',
     "wed": f'<path d="M40 140 Q120 80 200 140 T360 140" fill="none" stroke="{g}" stroke-width="3" opacity=".7"/>'
            f'<path d="M40 200 Q120 140 200 200 T360 200" fill="none" stroke="{g}" stroke-width="3" opacity=".5"/>'
            f'<path d="M40 260 Q120 200 200 260 T360 260" fill="none" stroke="{g}" stroke-width="3" opacity=".35"/>'
            f'<circle cx="200" cy="200" r="90" fill="{g}" opacity=".18"/>'
            f'<circle cx="200" cy="200" r="46" fill="{g}"/>',
     "thu": f'<g stroke="{g}" stroke-width="1.5" opacity=".5">'
            f'<line x1="100" y1="40" x2="100" y2="360"/><line x1="200" y1="40" x2="200" y2="360"/>'
            f'<line x1="300" y1="40" x2="300" y2="360"/><line x1="40" y1="120" x2="360" y2="120"/>'
            f'<line x1="40" y1="240" x2="360" y2="240"/></g>'
            f'<rect x="120" y="140" width="160" height="120" fill="none" stroke="{g}" stroke-width="3"/>'
            f'<circle cx="200" cy="200" r="34" fill="{g}"/>',
     "fri": f'<circle cx="150" cy="150" r="90" fill="{g}"/>'
            f'<circle cx="270" cy="250" r="60" fill="{g}" opacity=".6"/>'
            f'<polygon points="260,60 340,60 300,140" fill="{g}" opacity=".7"/>'
            f'<circle cx="150" cy="150" r="120" fill="none" stroke="{g}" stroke-width="3" opacity=".55"/>'
            f'<circle cx="270" cy="250" r="100" fill="none" stroke="{g}" stroke-width="3" opacity=".55"/>',
    }
    return bodies[key]

def svg(key, t):
    rb = min(t["rad"], 26)  # ボタン角丸（999=ピル→高さ半分相当）
    pill = 26 if t["rad"] >= 100 else rb
    # palette
    sw = ["primary "+t["primary"], "grad "+t["g0"], "grad "+t["g1"], "soft "+t["soft"], "ink "+t["heading"]]
    swatches = ""
    for i,(col) in enumerate([t["primary"], t["g0"], t["g1"], t["soft"], t["heading"]]):
        x = 80 + i*84
        swatches += f'<rect x="{x}" y="700" width="72" height="40" rx="8" fill="{col}" stroke="{t["border"]}"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="800" viewBox="0 0 1280 800" font-family="{JP}">
<defs>
 <linearGradient id="ga" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['g0']}"/><stop offset="1" stop-color="{t['g1']}"/></linearGradient>
 <linearGradient id="gb" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t['g0']}"/><stop offset="1" stop-color="{t['g1']}"/></linearGradient>
</defs>
<rect width="1280" height="800" fill="{t['bg']}"/>
<!-- header -->
<rect width="1280" height="72" fill="{t['surface']}"/>
<line x1="0" y1="72" x2="1280" y2="72" stroke="{t['border']}" stroke-width="1"/>
<rect x="80" y="18" width="36" height="36" rx="9" fill="url(#gb)"/>
<text x="98" y="43" fill="#fff" font-size="18" font-weight="700" text-anchor="middle">R</text>
<text x="128" y="38" fill="{t['heading']}" font-size="17" font-weight="700">Rion Lab Japan</text>
<text x="128" y="54" fill="{t['muted']}" font-size="9" letter-spacing="2">IT PRODUCT TOTAL SUPPORT</text>
<text x="720" y="46" fill="{t['heading']}" font-size="15">ホーム</text>
<text x="800" y="46" fill="{t['heading']}" font-size="15">サービス</text>
<text x="900" y="46" fill="{t['heading']}" font-size="15">会社情報</text>
<text x="1000" y="46" fill="{t['heading']}" font-size="15">DX研修ラボ</text>
<rect x="1090" y="20" width="110" height="32" rx="{pill}" fill="{t['primary']}"/>
<text x="1145" y="41" fill="#fff" font-size="13" text-anchor="middle">お問い合わせ</text>
<!-- hero left -->
<rect x="80" y="160" width="28" height="3" fill="{t['primary']}"/>
<text x="118" y="166" fill="{t['primary']}" font-size="13" letter-spacing="3" font-weight="700">IT PRODUCT TOTAL SUPPORT</text>
<text x="78" y="250" fill="{t['heading']}" font-size="62" font-weight="800">アイデアを、</text>
<text x="78" y="330" font-size="62" font-weight="800"><tspan fill="{t['primary']}">動くプロダクト</tspan><tspan fill="{t['heading']}">へ。</tspan></text>
<text x="80" y="392" fill="{t['muted']}" font-size="19">アプリ開発からWeb制作、バックエンド、DX研修まで。</text>
<text x="80" y="420" fill="{t['muted']}" font-size="19">日本とベトナム・ダナンの開発体制で、企画から運用まで</text>
<text x="80" y="448" fill="{t['muted']}" font-size="19">一気通貫であなたのビジネスを支えます。</text>
<rect x="80" y="486" width="220" height="52" rx="{pill}" fill="{t['primary']}"/>
<text x="190" y="519" fill="#fff" font-size="17" font-weight="700" text-anchor="middle">▸ まずは相談する</text>
<rect x="316" y="486" width="200" height="52" rx="{pill}" fill="none" stroke="{t['heading']}" stroke-width="2"/>
<text x="416" y="519" fill="{t['heading']}" font-size="17" font-weight="700" text-anchor="middle">サービスを見る →</text>
<!-- hero art -->
<g transform="translate(820,150) scale(0.95)">{art(key)}</g>
<!-- palette -->
<text x="80" y="688" fill="{t['muted']}" font-size="13" font-weight="700">PALETTE</text>
{swatches}
<!-- day badge -->
<rect x="980" y="700" width="220" height="40" rx="20" fill="{t['surface']}" stroke="{t['border']}"/>
<circle cx="1004" cy="720" r="6" fill="{t['primary']}"/>
<text x="1018" y="725" fill="{t['heading']}" font-size="14" font-weight="700">{t['name']} · {t['concept']}</text>
</svg>'''

paths=[]
for key,t in T.items():
    s = svg(key,t)
    out = f"{OUT}/preview_{key}.png"
    cairosvg.svg2png(bytestring=s.encode("utf-8"), write_to=out, output_width=1280, output_height=800)
    paths.append(out)
    print("wrote", out)
print("DONE", len(paths))
