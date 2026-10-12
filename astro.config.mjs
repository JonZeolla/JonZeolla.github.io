// @ts-check
import { defineConfig } from 'astro/config';

// https://docs.astro.build/en/reference/configuration-reference/
export default defineConfig({
  site: 'https://jonzeolla.com',
  // 'file' keeps /talks.html and the old *.html redirect stubs as real files, which is what GitHub Pages serves best.
  build: { format: 'file' },
  // Old Sphinx-era URLs that other sites link to. The labs keep their paths (Sphinx still builds them, see Taskfile).
  redirects: {
    '/meet-with-jon': 'https://zenable.io/jon',
    '/youtube': 'https://www.youtube.com/watch?v=oPhGKduOrKM&list=PLDvTIewuIyaKK2wk49iq5_rxUcNioSr0y&index=1',
    '/playlist': 'https://www.youtube.com/watch?v=6s6K2zelYQo&list=PLDvTIewuIyaKK2wk49iq5_rxUcNioSr0y&index=1',
    '/workshop': '/labs/container-security-101.html',  // served by Sphinx, merged into dist/ by the Taskfile
    '/resume': '/resume.pdf',
    '/about-me': '/',
  },
});
