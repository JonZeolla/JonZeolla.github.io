// Run with: npm test   (node --test, TypeScript via Node's built-in type stripping)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseContent, upcoming } from './content.ts';
import { studentsTaught, roundedDown } from './students.ts';
import { parseWidget } from './github.ts';

const c = parseContent();

test('parses the three tables from jz-content.md', () => {
  assert.ok(c.talks.length >= 82, `talks: ${c.talks.length}`);
  assert.ok(c.classes.length >= 61, `classes: ${c.classes.length}`);
  assert.ok(c.podcasts.length >= 24, `podcasts: ${c.podcasts.length}`);
  for (const rows of [c.talks, c.classes, c.podcasts]) for (const r of rows) {
    assert.match(r.date, /^\d{4}-\d{2}-\d{2}$/, `bad date ${r.date}`);
    assert.ok(r.title.length > 0 && r.event.length > 0);
    assert.ok(!r.title.includes('['), `unparsed markdown in ${r.title}`);
  }
});

test('resolves reference links and classifies them', () => {
  const csn = c.talks.find((t) => t.date === '2025-10-03');
  assert.ok(csn);
  assert.deepEqual(csn!.links.map((l) => l.label).sort(), ['Event', 'Slides', 'Watch']);
  const unknown = c.talks.find((t) => t.event === 'Unknown');
  assert.equal(unknown, undefined, 'the 2017-12 row should say Steel City InfoSec');
});

test('skips TBD/placeholder rows', () => {
  assert.equal(c.podcasts.find((p) => p.date === 'TBD'), undefined);
});

test('upcoming = strictly after today, soonest first', () => {
  const up = upcoming(c.classes, '2026-10-11');
  assert.deepEqual(up.slice(0, 2).map((e) => e.date), ['2026-10-19', '2026-10-26']);
  assert.ok(up.every((e) => e.date > '2026-10-11'));
});

test('students taught matches the 2026-10-11 tally', () => {
  assert.equal(studentsTaught(c.classes, '2026-10-11'), 1224);
  assert.equal(roundedDown(1224), '1,200+');
  assert.equal(roundedDown(999), '900+');
});

test('parseWidget reads GitHub contribution cells and tooltips', () => {
  const cell = (d: string, id: number, lvl: number) => `<td data-date="${d}" id="contribution-day-component-0-${id}" data-level="${lvl}"></td>`;
  const tip = (id: number, n: string) => `<tool-tip for="contribution-day-component-0-${id}">${n} contributions on x</tool-tip>`;
  let html = '';
  for (let i = 0; i < 365; i++) {
    const d = new Date(Date.UTC(2025, 9, 12 + i)).toISOString().slice(0, 10);
    html += cell(d, i, i % 5) + tip(i, i % 7 === 0 ? 'No' : String(i % 7));
  }
  const cal = parseWidget(html);
  assert.equal(cal.weeks.flat().length, 365);
  assert.equal(cal.total, [...Array(365).keys()].reduce((s, i) => s + (i % 7 === 0 ? 0 : i % 7), 0));
  assert.ok(cal.weeks.every((w) => w.length <= 7));
});
