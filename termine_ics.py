"""Kalenderabo der WSGE-Termine: liest wsge.de (Veranstaltungen, Ranglisten-Regatten, Yardstick-Regatten) und schreibt
site/termine.ics. Der Parser entspricht EventsService.swift in der App (gleiche Regeln, gleiche Seiten).
Schlägt der Abruf fehl oder findet der Parser auffällig wenig, bleibt die zuletzt veröffentlichte Datei erhalten.
Aufruf: python termine_ics.py [Ausgabedatei]"""
import os, re, sys, json, hashlib, datetime as dt, html as htmllib, urllib.request

BASE = 'http://wsge.de'
PUBLISHED = 'https://syring-digital.github.io/meinrved-termine/termine.ics'
KIND_TITLE = {'rved': 'RVED-Veranstaltung', 'yardstick': 'Yardstick-Regatta (Ederseemeisterschaft)',
              'ranglisten': 'Ranglisten-Regatta', 'verein': 'Vereinstermin'}


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 MeinRVED'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8')


def page(slug):
    return json.loads(fetch(f'{BASE}/wp-json/wp/v2/pages?slug={slug}&_fields=content'))[0]['content']['rendered']


def matches(pattern, text):
    return re.findall(pattern, text, re.S)


def plain(h, keep_breaks=False):
    s = re.sub(r'<br\s*/?>', '\n' if keep_breaks else ' ', h)
    s = re.sub(r'</(p|div|span)>', '\n' if keep_breaks else ' ', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = htmllib.unescape(s)
    lines = [re.sub(r'[ \t\u00A0]+', ' ', l).strip() for l in s.split('\n')]
    return ('\n' if keep_breaks else ' ').join(l for l in lines if l)


DATE_RE = re.compile(r'(\d{1,2})\.(?:(\d{1,2})\.)?(?:(\d{4}))?\s*(?:[-–]\s*(\d{1,2})\.(\d{1,2})\.(\d{4}))?')


def first_date(text):
    """Erstes Datum bzw. Zeitraum: (start, end, Spanne) oder None."""
    for m in DATE_RE.finditer(text):
        g = [int(x) if x else None for x in m.groups()]
        d1 = g[0]
        try:
            if g[3] and g[4] and g[5]:
                m1, y1 = g[1] or g[4], g[2] or g[5]
                s, e = dt.date(y1, m1, d1), dt.date(g[5], g[4], g[3])
                return s, max(s, e), m.span()
            if g[1] and g[2]:
                s = dt.date(g[2], g[1], d1)
                return s, s, m.span()
        except ValueError:
            continue
    return None


def ev(kind, title, d, place=None, classes=None, org=None, note=None, cancelled=False, url=None):
    return dict(kind=kind, title=title, start=d[0], end=d[1], place=place, classes=classes, organizer=org, note=note,
                cancelled=cancelled, url=url)


def parse_veranstaltungen(h):
    out = []
    for cell in matches(r'<td[^>]*>(.*?)</td>', h):
        text = plain(cell, True)
        if not text or text.lower().startswith('jeden'):
            continue
        d = first_date(text)
        if not d:
            continue
        rest = text[d[2][1]:].replace('\n', ' ').strip()
        parts = [p.strip() for p in rest.split('|') if p.strip()]
        if not parts:
            continue
        place = classes = org = None
        if len(parts) == 2: org = parts[1]
        elif len(parts) == 3: place, org = parts[1], parts[2]
        elif len(parts) >= 4: place, classes, org = parts[1], parts[2], parts[3]
        kind = 'rved' if 'RVED' in (org or '').upper() else 'verein'
        out.append(ev(kind, parts[0], d, place, classes, org, None, 'abgesagt' in text.lower(), f'{BASE}/veranstaltungen/'))
    return out


def parse_ranglisten(h):
    out = []
    for row in matches(r'<tr[^>]*>(.*?)</tr>', h):
        cells = matches(r'<td[^>]*>(.*?)</td>', row)
        if len(cells) < 2:
            continue
        logo, body = cells[0], cells[1]
        titles = matches(r'<b>(.*?)</b>', body)
        title = plain(titles[0]) if titles else ''
        if not title:
            continue
        text = plain(body, True)
        d = first_date(text)
        if not d:
            continue
        note = None
        i = text.find(title)
        if i >= 0:
            between = text[i + len(title):d[2][0]].strip()
            if between:
                note = between.replace('\n', ' ')
        org = (matches(r'alt="([^"]+)"', logo) or matches(r'clublogo/([A-Za-z0-9_-]+)\.', logo) or matches(r'uploads/([A-Za-z]+)\.png', logo) or [None])[0]
        m2s = (matches(r'href="(https?://[^"]*manage2sail[^"]*)"', body) or [None])[0]
        out.append(ev('ranglisten', title, d, None, None, org.upper() if org else None, note, 'abgesagt' in text.lower(), m2s or f'{BASE}/ranglisten-regatten/'))
    return out


def parse_yardstick(h):
    out = []
    for table in matches(r'<table[^>]*>(.*?)</table>', h):
        cells = matches(r'<td[^>]*>(.*?)</td>', table)
        if len(cells) < 2:
            continue
        logo, body = cells[0], cells[1]
        titles = matches(r'<b>(.*?)</b>', body)
        title = plain(titles[0]) if titles else ''
        if not title:
            continue
        text = plain(body, True)
        d = first_date(text)
        if not d:
            continue
        rest = text[d[2][1]:].strip().strip('()')
        org = (matches(r'clublogo/([A-Za-z0-9_-]+)\.', logo) or [None])[0]
        rg = (matches(r'regatta/\?rg=(\d+)', body) or [None])[0]
        info = f'{BASE}/regatta/?rg={rg}' if rg else f'{BASE}/regatta-index/'
        out.append(ev('yardstick', title, d, None, None, org.upper() if org else None, rest or None, 'abgesagt' in text.lower(), info))
    return out


def esc(s):
    return s.replace('\\', '\\\\').replace(';', '\;').replace(',', '\\,').replace('\n', '\\n')


def fold(line):
    out, cur, n = [], '', 0
    for ch in line:
        b = len(ch.encode('utf-8'))
        if n + b > 74:
            out.append(cur); cur, n = ' ', 1
        cur += ch; n += b
    out.append(cur)
    return '\r\n'.join(out)


def ics(events):
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Mein RVED//WSGE-Termine//DE', 'CALSCALE:GREGORIAN',
             'X-WR-CALNAME:Mein RVED Termine', 'X-WR-CALDESC:Termine von RVED und WSGE (Quelle: wsge.de). Alle Angaben ohne Gewähr.',
             'X-WR-TIMEZONE:Europe/Berlin', 'REFRESH-INTERVAL;VALUE=DURATION:PT12H', 'X-PUBLISHED-TTL:PT12H']
    for e in events:
        uid = hashlib.sha1(f"{e['kind']}|{e['title']}|{e['start']}".encode()).hexdigest()[:20]
        notes = [KIND_TITLE[e['kind']], f"Veranstalter: {e['organizer']}" if e['organizer'] else None, e['classes'], e['note'], e['url']]
        lines += ['BEGIN:VEVENT', f'UID:{uid}@meinrved.app', f'DTSTAMP:{now}',
                  f"DTSTART;VALUE=DATE:{e['start']:%Y%m%d}", f"DTEND;VALUE=DATE:{e['end'] + dt.timedelta(days=1):%Y%m%d}",
                  f"SUMMARY:{esc(e['title'])}"]
        if e['place']: lines.append(f"LOCATION:{esc(e['place'])}")
        lines.append(f"DESCRIPTION:{esc(chr(10).join(n for n in notes if n))}")
        if e['url']: lines.append(f"URL:{e['url']}")
        lines.append('END:VEVENT')
    lines.append('END:VCALENDAR')
    return '\r\n'.join(fold(l) for l in lines) + '\r\n'


def main(out_path):
    try:
        events = parse_veranstaltungen(page('veranstaltungen')) + parse_ranglisten(page('ranglisten-regatten')) + parse_yardstick(page('regatta-index'))
        events = [e for e in events if not e['cancelled']]
        events.sort(key=lambda e: (e['start'], e['title']))
        if len(events) < 10:
            raise RuntimeError(f'nur {len(events)} Termine gefunden, Seitenaufbau geändert?')
        text = ics(events)
        print(f'{len(events)} Termine')
    except Exception as err:
        print('Abruf fehlgeschlagen:', err, file=sys.stderr)
        text = fetch(PUBLISHED)          # zuletzt veröffentlichter Stand bleibt bestehen
        if 'BEGIN:VCALENDAR' not in text:
            raise
        print('Vorherigen Stand übernommen', file=sys.stderr)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site', 'termine.ics'))
