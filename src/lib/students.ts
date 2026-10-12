/**
 * "Engineers taught live": the sum, over every PAST row of the classes table, of the per-class
 * count in data/students.json. Classes missing from that file use its `default`. Future rows
 * are not counted. OnDemand recordings are listed in students.json as 0.
 * The rules and how to refresh the roster counts are in data/README.md.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { Entry } from './content';

interface StudentsFile { default: number; classes: Record<string, { students: number; source: string }> }
const file: StudentsFile = JSON.parse(readFileSync(resolve(process.cwd(), 'data/students.json'), 'utf8'));

export function studentsTaught(classes: Entry[], today: string): number {
  let total = 0;
  for (const c of classes) {
    if (c.date.toUpperCase() === 'TBD' || c.date > today) continue;
    total += file.classes[c.date]?.students ?? file.default;
  }
  return total;
}

/** 1224 -> "1,200+" : rounded down to the hundred, for display. */
export function roundedDown(n: number): string {
  return `${(Math.floor(n / 100) * 100).toLocaleString('en-US')}+`;
}
