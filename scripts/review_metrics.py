#!/usr/bin/env python3
"""Recalculate reported aggregate changes; no causal or synergy estimation."""
import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def two(value):
    return float(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def build():
    source = json.loads((ROOT / 'data/reviewed-metrics.json').read_text())
    rows = source['metrics']
    results = {}
    for row in rows:
        base, current = Decimal(str(row['base'])), Decimal(str(row['current']))
        if base <= 0:
            raise ValueError('Positive comparison base required')
        results[row['id'] + '_growth_pct'] = two((current / base - 1) * 100)
    by_id = {row['id']: row for row in rows}
    shares = []
    for key in ('base', 'current'):
        active = Decimal(str(by_id['active_cards'][key]))
        cards = Decimal(str(by_id['cards_in_force'][key]))
        if not 0 <= active <= cards:
            raise ValueError('Active cards must be within cards in force')
        shares.append(active / cards * 100)
    results['active_card_share_2022_pct'] = two(shares[0])
    results['active_card_share_2023_pct'] = two(shares[1])
    results['active_card_share_change_pp'] = two(shares[1] - shares[0])
    data = json.dumps(results, ensure_ascii=False, indent=2) + '\n'
    bars = []
    for row, y in zip(rows, (190, 275, 410, 495)):
        value = results[row['id'] + '_growth_pct']
        start = 500 + min(0, value) * 6
        width = abs(value) * 6
        color = '#168c88' if row['id'] in ('cards_in_force', 'active_cards') else '#5163a5'
        bars.append(f'<text x="48" y="{y+7}" class="label">{row["label"]}</text>'
                    f'<rect x="{start:.2f}" y="{y-16}" width="{width:.2f}" height="28" rx="4" fill="{color}"/>'
                    f'<text x="{max(500, start+width)+14:.2f}" y="{y+7}" class="value">{value:+.2f}%</text>')
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 650" role="img" aria-labelledby="title desc">
<title id="title">2023 年規模與獲利指標須分開解讀</title><desc id="desc">2023 相對 2022 的流通卡、有效卡、銀行合併營業費用及本期淨利變動。不同範圍不能直接識別併購綜效。</desc>
<rect width="1120" height="650" rx="20" fill="#f4f7fb"/>
<style>text{font-family:Arial,Noto Sans CJK TC,PingFang TC,sans-serif;fill:#172a43}.label{font-size:22px}.value{font-size:22px;font-weight:700}</style>
<text x="48" y="55" font-size="15" fill="#168c88">EVIDENCE REVIEW · 2023 vs 2022</text>
<text x="48" y="103" font-size="31" font-weight="700">規模成長與獲利，分開衡量</text>
<text x="48" y="149" font-size="17">信用卡業務指標 · 原小組表格，精確卡量未獨立重建</text>
<path d="M500 165V310 M500 385V530" stroke="#b7c5d8" stroke-width="2"/>
<text x="48" y="369" font-size="17">銀行與子公司合併財務 · 官方年報核對，2022 採重編比較數</text>
''' + '\n'.join(bars) + '''
<text x="48" y="580" font-size="19" font-weight="700">不同業務範圍，不能直接推論併購因果或信用卡獲利。</text>
<text x="48" y="618" font-size="15">來源：小組報告 PDF p.12；台北富邦銀行 2023 年報印刷 pp.196、209。數值見 data/。</text></svg>
'''
    return results, {'data/calculated-metrics.json': data, 'assets/growth-review.svg': svg}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Write derived JSON and SVG')
    args = parser.parse_args()
    results, outputs = build()
    for path, content in outputs.items():
        target = ROOT / path
        if args.write:
            target.write_text(content)
        elif not target.exists() or target.read_text() != content:
            raise SystemExit(f'Derived output differs: {path}; run with --write')
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print('Aggregate calculations consistent; no causal or realized-synergy validation.')


if __name__ == '__main__':
    main()
