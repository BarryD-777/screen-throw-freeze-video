#!/usr/bin/env python3
"""Apply approved replacement copy to the accepted V4 reveal clock; no media/API work."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def lines(copy: dict, key: str, maximum: int) -> list[str]:
    value = copy.get(key, [])
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ValueError(f'{key} must be a list of approved single-line strings')
    if len(value) > maximum:
        raise ValueError(f'{key} has {len(value)} rows; maximum is {maximum}. No copy was truncated.')
    result = [x.strip() for x in value]
    if any(not x or '\n' in x or '\r' in x for x in result):
        raise ValueError(f'{key} has an empty or multiline row')
    if len(set(result)) != len(result):
        raise ValueError(f'{key} has duplicate rows; do not pad the timeline with repeated claims')
    return result


def compose(copy: dict, clock: dict, audio_path: Path | None = None) -> dict:
    if not isinstance(copy, dict):
        raise ValueError('copy must be a JSON object')
    ingredients = lines(copy, 'ingredients', 8)
    absent = lines(copy, 'not_detected', 150)
    opening = copy.get('opening_text')
    if opening is not None and (not isinstance(opening, str) or not opening.strip() or len(opening.splitlines()) > 2):
        raise ValueError('opening_text must be null or one/two explicitly requested lines')
    titles = {key: copy.get(key, default) for key, default in
              [('left_title', '核心成分：'), ('right_title', '未检出成分')]}
    if any(not isinstance(x, str) or not x.strip() or '\n' in x or '\r' in x for x in titles.values()):
        raise ValueError('titles must be nonempty single-line strings')
    pages = []
    offset = 0
    for source_page in clock['right']['pages']:
        rows = []
        for source_row in source_page['rows']:
            if offset < len(absent):
                rows.append({**source_row, 'number': offset+1, 'text': absent[offset]})
            offset += 1
        pages.append({**source_page, 'rows': rows})
    return {
        'format': 'screen-throw-freeze-cues@1',
        'canvas': clock['canvas'],
        'audio': {**clock['audio'],
                  'source_asset': str(audio_path.resolve()) if audio_path is not None else None,
                  'requires_user_asset': audio_path is None},
        'events': clock['events'],
        'opening': {'text': opening, 'start_frame': 0, 'end_frame_exclusive': 101},
        'left': {'title': titles['left_title'] if ingredients else None,
                 'title_frame': clock['left']['title_frame'],
                 'rows': [{**slot, 'number': i+1, 'text': text}
                          for i, (text, slot) in enumerate(zip(ingredients, clock['left']['rows']))]},
        'right': {'title': titles['right_title'] if absent else None,
                  'title_frame': clock['right']['title_frame'], 'pages': pages},
        'used_slots': {'ingredients': len(ingredients), 'not_detected': len(absent)},
    }


def self_test(clock: dict) -> None:
    full = {'ingredients': [f'确认成分{i}' for i in range(8)],
            'not_detected': [f'确认检测陈述{i}' for i in range(150)]}
    data = compose(full, clock)
    assert data['canvas']['frames'] == 563 and data['events']['freeze_frame'] == 101
    assert data['audio']['start_frame'] == 0
    assert [r['start_frame'] for r in data['left']['rows']] == [101,106,111,118,124,130,135,141]
    expected = [r['start_frame'] for p in clock['right']['pages'] for r in p['rows']]
    actual = [r['start_frame'] for p in data['right']['pages'] for r in p['rows']]
    assert actual == expected and len(actual) == 150 and actual[-1] == 533
    assert [p['start_frame'] for p in data['right']['pages']] == [158,213,270,329,388,446,504]
    for row in data['left']['rows'] + [r for p in data['right']['pages'] for r in p['rows']]:
        changes = row['changes']
        assert changes[0][0] == row['start_frame'] and changes[-1][1] == 1
        assert all(a[0] < b[0] and a[1] <= b[1] for a,b in zip(changes, changes[1:]))
    short = compose({'ingredients':['一项','另一项'], 'not_detected':['未检出某检测项目']}, clock)
    assert len(short['left']['rows']) == 2 and sum(len(p['rows']) for p in short['right']['pages']) == 1
    assert short['left']['rows'][1]['changes'] == data['left']['rows'][1]['changes']
    assert short['opening']['text'] is None and short['canvas']['frames'] == 563
    assert short['right']['pages'][0]['rows'][0]['text'] == '未检出某检测项目'
    assert compose({}, clock)['right']['title'] is None
    assert data['audio']['source_asset'] is None and data['audio']['requires_user_asset']
    supplied = compose({}, clock, Path('licensed-track.m4a'))
    assert supplied['audio']['source_asset'] == str(Path('licensed-track.m4a').resolve())
    assert supplied['audio']['requires_user_asset'] is False
    for bad in [{'ingredients':['重复','重复']}, {'not_detected':['x']*151}, {'ingredients':['有\n换行']}]:
        try: compose(bad, clock)
        except ValueError: pass
        else: raise AssertionError('invalid copy was accepted')
    print('PASS: 563 frames, exact reveal anchors, unchanged curves for replacement text, no padding/truncation.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--copy', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--audio', type=Path,
                        help='Local licensed audio; omitted when only preparing cues')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    clock = read_json(ROOT/'assets/reveal-clock.json')
    if args.self_test:
        self_test(clock)
        return
    if args.copy is None or args.output is None:
        parser.error('--copy and --output are required')
    try:
        if args.audio is not None and not args.audio.is_file():
            raise ValueError('audio file does not exist; provide a local track you may use')
        output = compose(read_json(args.copy), clock, args.audio)
        if args.output.exists():
            raise ValueError('output already exists; use a new version path')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf8') as stream:
            stream.write(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    except (ValueError, OSError) as exc:
        parser.exit(2, f'{exc}\n')
    print(f'Wrote {args.output}; preserved original clock; copy facts must be checked separately.')


if __name__ == '__main__':
    main()
