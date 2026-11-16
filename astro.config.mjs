// @ts-check
import { defineConfig } from 'astro/config';

// https://docs.astro.build/en/reference/configuration-reference/
export default defineConfig({
  site: 'https://jonzeolla.com',
  // 'file' keeps /talks.html and the old *.html redirect stubs as real files, which is what GitHub Pages serves best.
  // The redirect stubs live in src/pages/[redirect].astro so each hit reaches Google Analytics before forwarding.
  build: { format: 'file' },
});
