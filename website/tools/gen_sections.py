#!/usr/bin/env python3
"""サービス/会社情報/お問い合わせ/スマホ版のプレビューPNGを生成（cairosvg・近似）。"""
import os, cairosvg

OUT = "/tmp/preview"; os.makedirs(OUT, exist_ok=True)
JP = "IPAGothic, 'DejaVu Sans', sans-serif"
# 代表テーマ＝Monday（他曜日は配色違いで同レイアウト）
t = dict(bg="#f6f9fe", surface="#ffffff", heading="#10243f", muted="#5a6675",
         primary="#1f6dff", soft="#e6efff", border="#e3eaf4", g0="#1f6dff", g1="#36c6ff")

def header():
    return f'''
<rect width="100%" height="72" fill="{t['surface']}"/>
<line x1="0" y1="72" x2="1280" y2="72" stroke="{t['border']}"/>
<rect x="80" y="18" width="36" height="36" rx="9" fill="url(#gb)"/>
<text x="98" y="43" fill="#fff" font-size="18" font-weight="700" text-anchor="middle">R</text>
<text x="128" y="38" fill="{t['heading']}" font-size="17" font-weight="700">Rion Lab Japan</text>
<text x="128" y="54" fill="{t['muted']}" font-size="9" letter-spacing="2">IT PRODUCT TOTAL SUPPORT</text>
<text x="720" y="46" fill="{t['heading']}" font-size="15">ホーム</text>
<text x="800" y="46" fill="{t['heading']}" font-size="15">サービス</text>
<text x="900" y="46" fill="{t['heading']}" font-size="15">会社情報</text>
<text x="1000" y="46" fill="{t['heading']}" font-size="15">DX研修ラボ</text>
<rect x="1090" y="20" width="110" height="32" rx="8" fill="{t['primary']}"/>
<text x="1145" y="41" fill="#fff" font-size="13" text-anchor="middle">お問い合わせ</text>'''

def page_hero(title, sub, crumb):
    return f'''
<text x="80" y="130" fill="{t['muted']}" font-size="13">ホーム / {crumb}</text>
<text x="78" y="190" fill="{t['heading']}" font-size="46" font-weight="800">{title}</text>
<text x="80" y="228" fill="{t['muted']}" font-size="17">{sub}</text>'''

def icon(x, y):
    return (f'<rect x="{x}" y="{y}" width="56" height="56" rx="14" fill="{t["soft"]}"/>'
            f'<rect x="{x+16}" y="{y+16}" width="24" height="24" rx="7" fill="{t["primary"]}"/>')

def card(x, y, w, h, title, lines):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{t["surface"]}" stroke="{t["border"]}"/>'
    s += icon(x+28, y+28)
    s += f'<text x="{x+28}" y="{y+118}" fill="{t["heading"]}" font-size="20" font-weight="700">{title}</text>'
    for i, ln in enumerate(lines):
        s += f'<text x="{x+28}" y="{y+150+i*24}" fill="{t["muted"]}" font-size="14">{ln}</text>'
    return s

def wrap_svg(h, inner):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="{h}" viewBox="0 0 1280 {h}" font-family="{JP}">
<defs><linearGradient id="gb" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t['g0']}"/><stop offset="1" stop-color="{t['g1']}"/></linearGradient></defs>
<rect width="1280" height="{h}" fill="{t['bg']}"/>{header()}{inner}</svg>'''

# ---- Services ----
services = [
 ("アプリ開発", ["iOS／Android／業務アプリの企画・", "設計・開発・公開まで伴走。"]),
 ("Web制作・開発", ["コーポレート・LP・Webアプリ。", "軽量・高速で運用しやすい設計。"]),
 ("バックエンド開発", ["API設計・DB・クラウド基盤。", "堅牢でスケールする土台を構築。"]),
 ("QC / 品質管理", ["テスト設計・実行・検証で", "リリース品質を担保します。"]),
 ("営業資料作成", ["提案・ピッチ・サービス資料を", "構成設計からデザインまで。"]),
 ("SNS運用", ["企画・制作・分析改善まで", "継続的に運用を支援します。"]),
 ("動画制作", ["紹介・採用・SNS向け動画を", "企画から編集まで一貫対応。"]),
 ("DX研修", ["生成AI活用・思考力強化で", "真のデジタル人材を育成。"]),
 ("技術コンサルティング", ["技術選定・要件整理・チーム", "立ち上げのご相談に対応。"]),
]
inner = page_hero("Services", "企画から開発、品質保証、運用、人材育成まで。必要な領域をまるごと。", "サービス")
gx, gy, cw, ch, gap = 80, 290, 360, 200, 30
for i, (ti, ls) in enumerate(services):
    r, c = divmod(i, 3)
    inner += card(gx + c*(cw+gap), gy + r*(ch+gap), cw, ch, ti, ls)
cairosvg.svg2png(bytestring=wrap_svg(290+3*(ch+gap)+20, inner).encode(), write_to=f"{OUT}/preview_services.png")
print("services")

# ---- Company ----
rows = [("会社名","株式会社Rion Lab Japan"),("設立","2019年10月24日"),
 ("代表者","代表取締役　小林 勇元"),("本社所在地","愛知県名古屋市中区"),
 ("支社","埼玉県川口市"),("開発拠点","ベトナム・ダナン（エンジニア約23名）"),
 ("事業内容","アプリ開発／Web制作／バックエンド／QC／DX研修 ほか"),
 ("関連事業","DX研修ラボ"),("お問い合わせ","お問い合わせフォーム")]
inner = page_hero("Company", "日本とベトナムをつなぐ開発体制で、ITプロダクトをトータルにサポート。", "会社情報")
inner += f'<text x="118" y="300" fill="{t["primary"]}" font-size="13" letter-spacing="2" font-weight="700">OVERVIEW</text>'
inner += f'<rect x="80" y="288" width="28" height="3" fill="{t["primary"]}"/>'
inner += f'<text x="78" y="350" fill="{t["heading"]}" font-size="34" font-weight="800">会社概要</text>'
ry = 390
for k, v in rows:
    inner += f'<text x="100" y="{ry+28}" fill="{t["heading"]}" font-size="16" font-weight="700">{k}</text>'
    inner += f'<text x="400" y="{ry+28}" fill="{t["muted"]}" font-size="16">{v}</text>'
    inner += f'<line x1="80" y1="{ry+48}" x2="1200" y2="{ry+48}" stroke="{t["border"]}"/>'
    ry += 56
cairosvg.svg2png(bytestring=wrap_svg(ry+40, inner).encode(), write_to=f"{OUT}/preview_company.png")
print("company")

# ---- Contact ----
inner = page_hero("Contact", "ご相談・お見積り・採用・協業など、お気軽にお問い合わせください。", "お問い合わせ")
fx, fw = 340, 600
def field(y, label, h=46):
    s = f'<text x="{fx}" y="{y}" fill="{t["heading"]}" font-size="15" font-weight="700">{label}</text>'
    s += f'<rect x="{fx}" y="{y+12}" width="{fw}" height="{h}" rx="10" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.5"/>'
    return s, y+12+h+24
inner += f'<rect x="{fx}" y="290" width="{fw}" height="44" rx="8" fill="#e8f8ee" stroke="#b6e7c9"/>'
inner += f'<text x="{fx+16}" y="318" fill="#0a7d3b" font-size="14">入力 → 送信で完了。管理画面の一覧に自動反映されます（PHP+SQLite）。</text>'
y = 360
for lab in ["お名前 ✱","会社名・団体名","メールアドレス ✱","電話番号","お問い合わせ種別"]:
    blk, y = field(y, lab); inner += blk
# message (tall)
inner += f'<text x="{fx}" y="{y}" fill="{t["heading"]}" font-size="15" font-weight="700">お問い合わせ内容 ✱</text>'
inner += f'<rect x="{fx}" y="{y+12}" width="{fw}" height="120" rx="10" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.5"/>'
y += 12+120+24
inner += f'<rect x="{fx}" y="{y}" width="20" height="20" rx="4" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.5"/>'
inner += f'<text x="{fx+30}" y="{y+16}" fill="{t["muted"]}" font-size="14">個人情報の取り扱いに同意します ✱</text>'
y += 44
inner += f'<rect x="{fx}" y="{y}" width="180" height="52" rx="8" fill="{t["primary"]}"/>'
inner += f'<text x="{fx+90}" y="{y+33}" fill="#fff" font-size="17" font-weight="700" text-anchor="middle">▸ 送信する</text>'
cairosvg.svg2png(bytestring=wrap_svg(y+90, inner).encode(), write_to=f"{OUT}/preview_contact.png")
print("contact")

# ---- Mobile (homepage hero, 390x844) ----
mw, mh = 390, 844
m = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{mw}" height="{mh}" viewBox="0 0 {mw} {mh}" font-family="{JP}">
<defs><linearGradient id="gb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['g0']}"/><stop offset="1" stop-color="{t['g1']}"/></linearGradient></defs>
<rect width="{mw}" height="{mh}" fill="{t['bg']}"/>
<rect width="{mw}" height="60" fill="{t['surface']}"/><line x1="0" y1="60" x2="{mw}" y2="60" stroke="{t['border']}"/>
<rect x="20" y="14" width="32" height="32" rx="8" fill="url(#gb)"/><text x="36" y="36" fill="#fff" font-size="16" font-weight="700" text-anchor="middle">R</text>
<text x="60" y="36" fill="{t['heading']}" font-size="15" font-weight="700">Rion Lab Japan</text>
<rect x="338" y="20" width="24" height="3" fill="{t['heading']}"/><rect x="338" y="28" width="24" height="3" fill="{t['heading']}"/><rect x="338" y="36" width="24" height="3" fill="{t['heading']}"/>
<rect x="20" y="110" width="24" height="3" fill="{t['primary']}"/>
<text x="54" y="116" fill="{t['primary']}" font-size="11" letter-spacing="2" font-weight="700">TOTAL SUPPORT</text>
<text x="18" y="180" fill="{t['heading']}" font-size="40" font-weight="800">アイデアを、</text>
<text x="18" y="230" font-size="40" font-weight="800"><tspan fill="{t['primary']}">動く</tspan><tspan fill="{t['heading']}">プロダクト</tspan></text>
<text x="18" y="280" fill="{t['heading']}" font-size="40" font-weight="800">へ。</text>
<text x="20" y="324" fill="{t['muted']}" font-size="14">アプリ開発からWeb制作、DX研修まで。</text>
<text x="20" y="346" fill="{t['muted']}" font-size="14">企画から運用まで一気通貫で支えます。</text>
<rect x="20" y="380" width="350" height="50" rx="8" fill="{t['primary']}"/><text x="195" y="411" fill="#fff" font-size="16" font-weight="700" text-anchor="middle">▸ まずは相談する</text>
<rect x="20" y="442" width="350" height="50" rx="8" fill="none" stroke="{t['heading']}" stroke-width="2"/><text x="195" y="473" fill="{t['heading']}" font-size="16" font-weight="700" text-anchor="middle">サービスを見る →</text>
<g transform="translate(75,520) scale(0.6)">
 <rect x="40" y="40" width="320" height="320" rx="10" fill="none" stroke="url(#gb)" stroke-width="2" opacity=".5"/>
 <rect x="70" y="70" width="120" height="120" rx="8" fill="url(#gb)"/>
 <rect x="210" y="70" width="120" height="120" rx="8" fill="url(#gb)" opacity=".55"/>
 <rect x="70" y="210" width="120" height="120" rx="8" fill="url(#gb)" opacity=".35"/>
 <circle cx="270" cy="270" r="60" fill="url(#gb)"/>
</g>
<rect x="210" y="788" width="160" height="36" rx="18" fill="{t['surface']}" stroke="{t['border']}"/>
<circle cx="232" cy="806" r="6" fill="{t['primary']}"/><text x="246" y="811" fill="{t['heading']}" font-size="12" font-weight="700">Monday · Fresh Start</text>
</svg>'''
cairosvg.svg2png(bytestring=m.encode(), write_to=f"{OUT}/preview_mobile.png", output_width=mw*2, output_height=mh*2)
print("mobile")
print("DONE")
