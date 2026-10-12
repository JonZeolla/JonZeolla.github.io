/**
 * GitHub contribution calendar for the home page.
 *
 * Source: the public widget at https://github.com/users/<login>/contributions. Its total matches the
 * number shown on the profile to a logged-out visitor; the GraphQL API counts differently (fewer),
 * so it is not used. Fetched at build time; if the fetch fails (offline, rate limit) the committed
 * snapshot in src/data/github-contributions.json is used so the build never breaks. Refresh the
 * snapshot by running a build with network access and copying the printed JSON, or let the daily
 * deploy do it.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

export type Day = [date: string, count: number, level: number]; // date is YY-MM-DD
export interface Calendar { total: number; weeks: Day[][]; source: string; fetchedAt: string }

const LOGIN = 'jonzeolla';
const SNAPSHOT = resolve(process.cwd(), 'src/data/github-contributions.json');

export function parseWidget(html: string): Omit<Calendar, 'fetchedAt'> {
  const cells = [...html.matchAll(/<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*id="(contribution-day-component-\d+-\d+)"[^>]*data-level="(\d)"/g)];
  const counts = new Map<string, number>();
  for (const m of html.matchAll(/<tool-tip[^>]*for="(contribution-day-component-\d+-\d+)"[^>]*>\s*(\d+|No) contribution/g)) {
    counts.set(m[1], m[2] === 'No' ? 0 : Number(m[2]));
  }
  if (cells.length < 300) throw new Error(`contributions widget: only ${cells.length} day cells found`);
  const days: Day[] = cells
    .map(([, date, id, level]) => [date.slice(2), counts.get(id) ?? 0, Number(level)] as Day)
    .sort((a, b) => a[0].localeCompare(b[0]));
  const weeks: Day[][] = [];
  for (const d of days) {
    const dow = new Date(`20${d[0]}T12:00:00Z`).getUTCDay();
    if (dow === 0 || weeks.length === 0) weeks.push([]);
    weeks[weeks.length - 1].push(d);
  }
  return { total: days.reduce((s, d) => s + d[1], 0), weeks, source: `github.com/users/${LOGIN}/contributions` };
}

export async function loadCalendar(): Promise<Calendar> {
  try {
    const res = await fetch(`https://github.com/users/${LOGIN}/contributions`, {
      headers: { 'user-agent': 'jonzeolla.com build (https://jonzeolla.com)' },
      signal: AbortSignal.timeout(15_000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const cal: Calendar = { ...parseWidget(await res.text()), fetchedAt: new Date().toISOString() };
    writeFileSync(SNAPSHOT, JSON.stringify(cal));
    return cal;
  } catch (err) {
    console.warn(`[github] using snapshot: ${(err as Error).message}`);
    return JSON.parse(readFileSync(SNAPSHOT, 'utf8')) as Calendar;
  }
}
