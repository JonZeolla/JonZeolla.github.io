/**
 * Parses docs/ref/jz-content.md, the single source for talks, classes, and podcasts.
 *
 * The file has three markdown tables under `# Event Presentations`, `# My Training Classes`,
 * and `# Podcasts and Live Streams`, each `| Date | Event | Title |`, plus reference-style
 * link definitions (`[ref]: url "title"`) at the end of each section. Dates are YYYY-MM-DD;
 * an unknown day is written as 00. Rows dated TBD or titled "Placeholder" are skipped.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export type LinkKind = 'Watch' | 'Listen' | 'Slides' | 'Event' | 'Link';
export interface Link { label: LinkKind; url: string }
export interface Entry { date: string; event: string; title: string; links: Link[] }
export interface Content { talks: Entry[]; classes: Entry[]; podcasts: Entry[] }

// Resolved from the project root: Astro bundles this module under dist/.prerender, so import.meta.url is not usable.
const SOURCE = resolve(process.cwd(), 'docs/ref/jz-content.md');

function classify(label: string, url: string): LinkKind {
  const u = url.toLowerCase(), l = label.toLowerCase();
  if (u.includes('youtu') || u.includes('sans.org/webcasts')) return 'Watch';
  if (u.includes('spotify') || u.includes('podcast') || u.includes('podbean')) return 'Listen';
  if (l === 'slides' || u.includes('monopreso') || u.includes('docs.google.com/presentation')) return 'Slides';
  if (l === 'event') return 'Event';
  return 'Link';
}

/** Strip markdown/HTML links from a cell, collecting their targets. */
function unlink(cell: string, refs: Map<string, string>): { text: string; links: { label: string; url: string }[] } {
  const links: { label: string; url: string }[] = [];
  let text = cell.replace(/\[([^\]]+)\]\[([^\]]*)\]/g, (_m, label: string, ref: string) => {
    const url = refs.get((ref || label).toLowerCase());
    if (url) links.push({ label, url });
    return label;
  });
  text = text.replace(/<a href="([^"]+)"[^>]*>([^<]+)<\/a>/g, (_m, url: string, label: string) => {
    links.push({ label, url });
    return label;
  });
  text = text.replace(/\{sup\}`([^`]+)`/g, '$1').replace(/\s*\((Slides)\)/g, '').trim();
  return { text, links };
}

export function parseContent(markdown = readFileSync(SOURCE, 'utf8')): Content {
  const refs = new Map<string, string>();
  for (const m of markdown.matchAll(/^\[([^\]]+)\]:\s*(\S+)/gm)) refs.set(m[1].toLowerCase(), m[2]);

  const sections: Record<string, Entry[]> = {};
  for (const section of markdown.split(/^# /m).slice(1)) {
    const nl = section.indexOf('\n');
    const name = section.slice(0, nl).trim();
    const rows: Entry[] = [];
    for (const line of section.slice(nl + 1).split('\n')) {
      if (!line.startsWith('|') || line.startsWith('| Date') || /^[\s|:-]+$/.test(line)) continue;
      const cells = line.replace(/^\||\|$/g, '').split('|').map((c: string) => c.trim());
      if (cells.length < 3) continue;
      const [date, eventCell, titleCell] = cells;
      const ev = unlink(eventCell, refs), ti = unlink(titleCell, refs);
      if (date.toUpperCase() === 'TBD' || ti.text.includes('Placeholder')) continue;
      const links: Link[] = ti.links.map((l) => ({ label: classify(l.label, l.url), url: l.url }));
      if (ev.links[0]) links.push({ label: 'Event', url: ev.links[0].url });
      rows.push({ date, event: ev.text, title: ti.text, links });
    }
    sections[name] = rows;
  }
  const pick = (n: string) => {
    if (!sections[n]) throw new Error(`jz-content.md: missing section "# ${n}"`);
    return sections[n];
  };
  return { talks: pick('Event Presentations'), classes: pick('My Training Classes'), podcasts: pick('Podcasts and Live Streams') };
}

/** Rows dated strictly after `today` (YYYY-MM-DD), oldest first. A day of 00 compares as the 1st. */
export function upcoming(entries: Entry[], today: string): Entry[] {
  return entries
    .filter((e) => e.date.replace(/-00$/, '-01') > today)
    .sort((a, b) => a.date.localeCompare(b.date));
}

export const content: Content = parseContent();
