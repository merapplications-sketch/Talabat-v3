/* AH-03: owner-supplied app branding. Core/auth/data code remains untouched. */
(function () {
  'use strict';
  if (window.TALABOT_BRAND) return;

  const source = () => 'assets/brand/logo-talabot-' + (TLB.lang() === 'en' ? 'en' : 'ru') + '.webp';
  function html(className = '') {
    return '<img data-talabot-logo class="' + className.replace(/[^a-zA-Z0-9 _-]/g, '') +
      '" src="' + source() + '" alt="Talabot">';
  }
  function setImage(image) {
    const src = source();
    if (image.getAttribute('src') !== src) image.setAttribute('src', src);
    if (image.alt !== 'Talabot') image.alt = 'Talabot';
    if (!image.hasAttribute('data-talabot-logo')) image.setAttribute('data-talabot-logo', '');
  }
  function makeImage(className) {
    const image = document.createElement('img');
    image.className = className;
    setImage(image);
    return image;
  }
  function sync() {
    document.querySelectorAll('[data-talabot-logo],.a-header .a-brand img,.a-auth-brand img').forEach(setImage);

    // Core owns auth forms. Replace only its decorative brand block; retain its tagline.
    const overlay = document.getElementById('tlb-ov');
    const brand = overlay && [...overlay.children].find(node =>
      node.style.textAlign === 'center' && !node.classList.contains('a-auth-brand'));
    if (brand && !brand.querySelector('[data-talabot-logo]')) {
      const tagline = brand.querySelector('[data-i18n="tagline"]');
      brand.replaceChildren(makeImage('talabot-auth-logo'));
      if (tagline) brand.append(tagline);
    }

    // Driver keeps its existing auth wrapper and MutationObserver.
    const boot = document.getElementById('tlb-boot');
    if (boot && !boot.querySelector('[data-talabot-logo]')) boot.prepend(makeImage('talabot-loading-logo'));

    // The merchant's desktop navigation previously painted a text-only pseudo-logo.
    const nav = document.querySelector('body.st-merchant .nav');
    if (nav && !nav.querySelector('.talabot-nav-logo')) nav.prepend(makeImage('talabot-nav-logo'));
  }

  const style = document.createElement('style');
  style.id = 'talabot-brand-brief31b';
  style.textContent = `
    /* AH-04: fit the 36px Home mark in its own row without overlapping the address. */
    #app .d6h .d6-hh .d6-hr{grid-template-rows:36px 44px}
    #app .d6h .d6-hh .d6-hr>.d6-logo{width:auto;height:36px;max-width:100%}
    .talabot-auth-logo{display:block;width:180px;height:auto;margin:0 auto 12px;object-fit:contain}
    .talabot-loading-logo{display:block;width:150px;height:auto;margin:0 auto 18px;object-fit:contain}
    /* Previous driver logo: 104px wide, original 2404x504 canvas. */
    .a-header .a-brand img{width:104px;height:21.8px;object-fit:contain;object-position:left}
    .talabot-side-logo{display:block;width:auto;height:23px;max-width:160px;object-fit:contain;background:#fff;border-radius:4px;padding:2px 5px;box-sizing:content-box}
    .talabot-nav-logo{display:none}
    body.st-merchant .nav::before{content:none}
    @media(min-width:1024px){
      body.st-merchant .nav>.talabot-nav-logo{display:block;position:absolute;left:22px;top:26px;width:auto;height:23px;max-width:160px;object-fit:contain;background:#fff;border-radius:4px;padding:2px 5px;box-sizing:content-box}
    }
  `;
  document.head.append(style);
  window.TALABOT_BRAND = Object.freeze({source, html, sync});

  // setLang updates both TLB listeners and the document language. Observe new
  // render/overlay nodes only; changing our own image attributes cannot loop.
  TLB.on(sync);
  new MutationObserver(sync).observe(document.documentElement, {attributes: true, attributeFilter: ['lang']});
  new MutationObserver(records => {
    if (records.some(record => record.addedNodes.length)) sync();
  }).observe(document.body, {childList: true, subtree: true});
  sync();
}());
