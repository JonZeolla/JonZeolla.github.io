// /sitemap.xml — every page Google should index. Labs come from docs/labs/*.md, so a new lab is listed automatically.
import { readdirSync } from 'node:fs';
import type { APIRoute } from 'astro';
import { site } from '../lib/site';

export const GET: APIRoute = () => {
  const labs = readdirSync('docs/labs')
    .filter((file) => file.endsWith('.md'))
    .map((file) => `/labs/${file.replace(/\.md$/, '.html')}`);
  const urls = ['/', '/talks.html', '/llms.txt', '/labs/', ...labs]
    .map((path) => `  <url><loc>${site.url}${path}</loc></url>`)
    .join('\n');
  const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;
  return new Response(body, { headers: { 'content-type': 'application/xml; charset=utf-8' } });
};
