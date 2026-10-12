/**
 * The Speaking section: one featured recording and a 3x2 grid, chosen by hand.
 * `thumb` is a file under public/yt/. YouTube stills are fetched with scripts/thumbnails.sh;
 * talks whose YouTube art is stock imagery get a rendered card instead (same script).
 * Order of `grid` is the display order; keep the two orange SANS stills apart.
 */
export interface Featured { title: string; event: string; year: number; watch: string; slides?: string; thumb: string; alt?: string }

export const featured: Featured = {
  title: 'How I learned to stop worrying and love vibe coding: security edition',
  event: 'SANS CloudSecNext 2025',
  year: 2025,
  watch: 'https://www.youtube.com/watch?v=XaosRsgGSX8',
  slides: 'https://github.com/JonZeolla/monopreso/tree/main/presentations/2025-10-cloudsecnext',
  thumb: '/yt/XaosRsgGSX8.jpg',
  alt: 'Jon on stage at SANS CloudSecNext 2025',
};

export const featuredDescription =
  'Why AI-written code looks finished and isn’t, and how policy as code turns that into guardrails enforced on every commit, across every repository.';

export const grid: Featured[] = [
  { title: 'Agentic Code Review in GitLab & GitHub', event: 'SANS webcast', year: 2026, watch: 'https://youtu.be/MzsmDlQe9S8', thumb: '/yt/MzsmDlQe9S8.jpg' },
  { title: 'Your developers’ AI code looks perfect, until it hits production', event: 'The Sunny Side podcast', year: 2026, watch: 'https://youtu.be/pT8Jgl5RZ18', thumb: '/yt/pT8Jgl5RZ18.jpg' },
  { title: 'Vibe coding safety course', event: 'Cloud Security Alliance Pittsburgh', year: 2025, watch: 'https://www.youtube.com/watch?v=6s6K2zelYQo', thumb: '/yt/6s6K2zelYQo.jpg' },
  { title: 'Love vibe coding: security edition', event: 'BSides Pittsburgh', year: 2025, watch: 'https://www.youtube.com/watch?v=oPhGKduOrKM', thumb: '/yt/bsides-2025.png' },
  { title: 'Cloud Native GRC', event: 'CloudNativeSecurityCon', year: 2024, watch: 'https://youtu.be/HvLkkrNFiK8', thumb: '/yt/HvLkkrNFiK8.jpg' },
  { title: 'Securing Coding Agents with MCP', event: 'SANS webcast', year: 2026, watch: 'https://youtu.be/5QgLbuSNN58', thumb: '/yt/5QgLbuSNN58.jpg' },
];

/** Course codes in the classes table expand to full names in "Upcoming". */
export const courseNames: Record<string, string> = {
  SEC540: 'SEC540: Cloud Security and DevSecOps Automation',
  SEC545: 'SEC545: GenAI and LLM Application Security',
};
