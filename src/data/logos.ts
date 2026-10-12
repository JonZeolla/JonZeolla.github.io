/**
 * "Trusted by engineers at": employers of SANS students (from the roster tallies, see data/README.md)
 * plus workshop clients, chosen by hand. Each slug has two files: public/wm/<slug>.svg (original brand
 * colors, light mode) and public/wm-dark/<slug>.svg (dark fills recolored to near-white, brand colors
 * kept; see scripts/README.md for the recolor rule). `tall` marks square-ish marks that need more height.
 * Two rows scroll in opposite directions; keep them roughly balanced.
 */
export interface Logo { slug: string; name: string; tall?: boolean }

export const logoRows: Logo[][] = [
  [
    { slug: 'amazon', name: 'Amazon' }, { slug: 'google', name: 'Google' }, { slug: 'microsoft', name: 'Microsoft' },
    { slug: 'apple', name: 'Apple', tall: true }, { slug: 'accenture', name: 'Accenture' }, { slug: 'deloitte', name: 'Deloitte' },
    { slug: 'ey', name: 'EY', tall: true }, { slug: 'exxonmobil', name: 'ExxonMobil' }, { slug: 'walmart', name: 'Walmart' },
    { slug: 'unitedairlines', name: 'United Airlines', tall: true }, { slug: 'shopify', name: 'Shopify' }, { slug: 'clickup', name: 'ClickUp' },
  ],
  [
    { slug: 'capitalone', name: 'Capital One' }, { slug: 'visa', name: 'Visa' }, { slug: 'bankofamerica', name: 'Bank of America' },
    { slug: 'morganstanley', name: 'Morgan Stanley' }, { slug: 'nasa', name: 'NASA', tall: true }, { slug: 'siemens', name: 'Siemens' },
    { slug: 'tmobile', name: 'T-Mobile' }, { slug: 'cisco', name: 'Cisco', tall: true }, { slug: 'dell', name: 'Dell' },
    { slug: 'bloomberg', name: 'Bloomberg' }, { slug: 'pepsico', name: 'PepsiCo' },
  ],
];
