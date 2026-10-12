// /llms.txt — what the site is and where things are, for LLMs and agents (https://llmstxt.org).
// Generated from the same data as the pages, so the counts never drift.
import type { APIRoute } from 'astro';
import { content } from '../lib/content';
import { site, counts } from '../lib/site';
import { modules } from '../data/labs';

export const GET: APIRoute = () => {
  const recent = [...content.talks, ...content.podcasts]
    .filter((t) => t.links.some((l) => l.label === 'Watch' || l.label === 'Listen'))
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 4)
    .map((t) => `${t.title} (${t.event}, ${t.date.slice(0, 4)})`)
    .join(', ');
  const body = `# ${site.name}

> Founder of Zenable, Agentic AI Foundation Ambassador, self-described ${site.nickname}. ${site.mission} Builds verifiers for software (twenty years; machine learning since 2015; exclusively for coding agents since 2023) and teaches engineers to build their own.

Jon Zeolla is based in ${site.location}. In his day job at Zenable he builds managed, self-improving verifiers that mold themselves to a company's unique requirements. In his classes he teaches engineers how to do the same. He speaks at SANS, CSA, ISACA, BSides, DevOpsDays, KubeCon, and CloudNativeSecurityCon, and runs private hands-on workshops for engineering teams.

## Contact and profiles

- [Talk to Jon](${site.links.meet}): book time for talks, workshops, or a strategy session
- [Resume](${site.url}${site.links.resume}): one-page PDF
- [GitHub](${site.links.github})
- [LinkedIn](${site.links.linkedin})
- [X](${site.links.x})
- [YouTube playlist](${site.links.youtube}): recorded talks

## Speaking

- [All talks, classes, and podcasts](${site.url}/talks.html): ${counts.talks} talks, ${counts.classes} classes, ${counts.podcasts} podcasts since 2011, with Watch and Slides links
- [Slides (monopreso)](${site.links.slides}): source for most recent decks
- Recent recordings: ${recent}

## Teaching

${counts.studentsRounded} engineers taught live (in person or live online; recordings not counted), across ${counts.classes} classes since 2013. Instructor for SANS SEC540 and SEC545; private AI-Native Software Development workshops for engineering teams.

## Hands-on labs

${modules.reduce((n, m) => n + m.labs.length, 0)} labs, more than 40 hours of hands-on content, run as private workshops for engineering teams. Modules:

${modules.map((m) => `- ${m.title}: ${m.topics.join(', ')}`).join('\n')}

Public lab environments: ${site.links.labsRepo}

## Background

- Founder & CEO, Zenable (2023–)
- Agentic AI Foundation Ambassador, inaugural cohort (2026–)
- SANS Certified Instructor, SEC540 and SEC545 (2022–); IANS faculty
- CNCF TAG Security member (2020–2026); CNCF Ambassador (2023–2026)
- Co-founder & CTO, Seiso, sold in 2026 (2017–2026)
- Principal Information Security Engineer, Carnegie Mellon University (2014–2020)
- Apache Software Foundation committer, Apache Metron (2017–)
`;
  return new Response(body, { headers: { 'content-type': 'text/plain; charset=utf-8' } });
};
