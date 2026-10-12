/**
 * Site-wide facts and the numbers shown on the page. Everything derived is computed here from
 * docs/ref/jz-content.md and data/students.json so the home page, /talks, and /llms.txt agree.
 * The two hand-maintained numbers (labs built, public repos) carry their formula next to them.
 */
import { content, upcoming } from './content';
import { studentsTaught, roundedDown } from './students';

export const site = {
  name: 'Jon Zeolla',
  url: 'https://jonzeolla.com',
  location: 'Pittsburgh, PA',
  roles: ['Founder, Zenable', 'AAIF Ambassador'],
  nickname: 'AI Janitor',
  mission: 'I’m on a mission to make AI Correct, Observable, and Conformant.',
  links: {
    github: 'https://github.com/jonzeolla',
    linkedin: 'https://linkedin.com/in/jonzeolla',
    x: 'https://twitter.com/jonzeolla',
    youtube: 'https://www.youtube.com/playlist?list=PLDvTIewuIyaKK2wk49iq5_rxUcNioSr0y',
    meet: 'https://zenable.io/jon',
    resume: '/resume.pdf',
    slides: 'https://github.com/JonZeolla/monopreso',
    zenable: 'https://zenable.io',
    labsRepo: 'https://github.com/Zenable-io/labs',
  },
} as const;

/** Build date, YYYY-MM-DD (UTC). The daily deploy rebuilds, so "upcoming" and "past" roll over on their own. */
export const today = new Date().toISOString().slice(0, 10);

// labs built = next-gen-governance labs (services/ui_frontend/src/lib/labs/content/labs/*.mdx, 31 on 2026-10-11)
//            + jonzeolla.com labs (docs/labs/*.md, 3)
//            + https://github.com/JonZeolla?tab=repositories&q=lab (11, excluding the deprecated `Lab` and `lab-resources`)
export const labsBuilt = 45;
// github.com/jonzeolla profile, public repositories
export const publicRepos = 174;

const students = studentsTaught(content.classes, today);
export const counts = {
  talks: content.talks.length,
  classes: content.classes.length,
  podcasts: content.podcasts.length,
  students,
  studentsRounded: roundedDown(students),
  labsBuilt,
  publicRepos,
};

/** Future talks and classes, soonest first. */
export const upcomingAll = [
  ...upcoming(content.talks, today).map((e) => ({ ...e, kind: 'talk' as const })),
  ...upcoming(content.classes, today).map((e) => ({ ...e, kind: 'class' as const })),
].sort((a, b) => a.date.localeCompare(b.date));
