// Google Analytics behind a cookie banner (vanilla-cookieconsent), shared by the Astro pages, the redirect stubs
// and the Sphinx labs. EEA/UK/Swiss visitors get no analytics cookies until they accept; everyone else can opt out
// from "Cookie settings" in the footer.
(function () {
  var GA = 'G-EZSNDVQWPT';
  var OPT_IN = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU',
    'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'IS', 'LI', 'NO', 'GB', 'CH'];
  // Set on the redirect stubs: count the hit, then forward.
  var to = document.currentScript && document.currentScript.dataset.to;
  var gone = false;
  function go() { if (!gone) { gone = true; location.replace(to); } }
  // Forward even if gtag.js is blocked (its callback never fires) or anything below fails.
  if (to) setTimeout(go, 2000);
  // shortcut: guesses EU visitors from their timezone to decide who sees the banner; anyone it misses still gets
  // Google's region default below (no cookies), so it errs toward privacy. Upgrade to a geo-IP lookup if that matters.
  var eu = /^Europe\//.test(Intl.DateTimeFormat().resolvedOptions().timeZone || '');

  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  var off = { ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied', analytics_storage: 'denied' };
  gtag('consent', 'default', Object.assign({ region: OPT_IN }, off));
  gtag('consent', 'default', Object.assign({}, off, { analytics_storage: 'granted' }));
  gtag('js', new Date());
  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA;
  document.head.appendChild(s);

  // Only an explicit choice overrides the defaults above.
  function sync() {
    if (CookieConsent.validConsent()) {
      gtag('consent', 'update', { analytics_storage: CookieConsent.acceptedCategory('analytics') ? 'granted' : 'denied' });
    }
  }

  function theme() {
    var t = document.documentElement.getAttribute('data-theme');
    document.documentElement.classList.toggle('cc--darkmode', t ? t === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches);
  }
  theme();
  document.addEventListener('themechange', theme);

  CookieConsent.run({
    autoShow: eu && !to,
    guiOptions: { consentModal: { layout: 'box', position: 'bottom right' } },
    onFirstConsent: sync,
    onChange: sync,
    categories: { analytics: { enabled: !eu } },
    language: {
      default: 'en',
      translations: {
        en: {
          consentModal: {
            title: 'Cookies',
            description: 'I use Google Analytics cookies to see which pages people read. Google processes that data for me. Nothing is sent to advertisers.',
            acceptAllBtn: 'Accept',
            acceptNecessaryBtn: 'Decline',
          },
          preferencesModal: {
            title: 'Cookie settings',
            acceptAllBtn: 'Accept',
            acceptNecessaryBtn: 'Decline',
            savePreferencesBtn: 'Save',
            sections: [{
              title: 'Analytics',
              description: 'Google Analytics cookies (_ga, _ga_*) that count visits and pages read. Kept up to 2 years.',
              linkedCategory: 'analytics',
            }],
          },
        },
      },
    },
  }).then(function () {
    sync();
    if (!to) return gtag('config', GA);
    gtag('config', GA, { send_page_view: false });
    gtag('event', 'page_view', { event_callback: go, event_timeout: 1500 });
  });
})();
