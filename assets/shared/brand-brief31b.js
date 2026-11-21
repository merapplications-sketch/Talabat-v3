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
  // AH-05: padding belongs to the white host, so the artwork itself stays 44px high.
  function pill(className = '') {
    const wrapper = document.createElement('span');
    wrapper.className = 'talabot-brand-pill ' + className.replace(/[^a-zA-Z0-9 _-]/g, '');
    wrapper.append(makeImage('talabot-pill-logo'));
    return wrapper;
  }
  function wrapImage(image, className) {
    if (image.closest('.talabot-brand-pill')) return;
    const wrapper = pill(className);
    wrapper.replaceChildren();
    image.before(wrapper);
    wrapper.append(image);
  }
  function sync() {
    document.querySelectorAll('[data-talabot-logo],.a-header .a-brand img,.a-auth-brand img').forEach(setImage);

    // Core owns auth forms. Replace only its decorative brand block; retain its tagline.
    const overlay = document.getElementById('tlb-ov');
    const brand = overlay && [...overlay.children].find(node =>
      node.style.textAlign === 'center' && !node.classList.contains('a-auth-brand'));
    if (brand && !brand.querySelector('[data-talabot-logo]')) {
      const tagline = brand.querySelector('[data-i18n="tagline"]');
      brand.replaceChildren(pill('talabot-auth-pill'));
      if (tagline) brand.append(tagline);
    }
    if (brand) brand.querySelectorAll('img[data-talabot-logo]').forEach(image => wrapImage(image, 'talabot-auth-pill'));
    document.querySelectorAll('.a-auth-brand img').forEach(image => wrapImage(image, 'talabot-auth-pill'));

    // Driver keeps its existing auth wrapper and MutationObserver.
    const boot = document.getElementById('tlb-boot');
    if (boot && !boot.querySelector('[data-talabot-logo]')) boot.prepend(pill('talabot-loading-pill'));

    // The merchant's desktop navigation previously painted a text-only pseudo-logo.
    const nav = document.querySelector('body.st-merchant .nav');
    if (nav && !nav.querySelector('.talabot-nav-pill')) nav.prepend(pill('talabot-nav-pill'));
    document.querySelectorAll('.sbrand img[data-talabot-logo]').forEach(image => wrapImage(image, 'talabot-side-pill'));
  }

  const style = document.createElement('style');
  style.id = 'talabot-brand-brief31b';
  style.textContent = `
    /* AH-04: fit the 36px Home mark in its own row without overlapping the address. */
    #app .d6h .d6-hh .d6-hr{grid-template-rows:36px 44px}
    #app .d6h .d6-hh .d6-hr>.d6-logo{width:auto;height:36px;max-width:100%}
    .talabot-brand-pill{display:inline-flex;align-items:center;justify-content:center;flex:none;width:max-content;max-width:100%;padding:12px 20px;box-sizing:border-box;border-radius:20px;background:#fff;box-shadow:0 4px 18px rgba(23,36,60,.10)}
    .talabot-brand-pill>img[data-talabot-logo],#tlb-ov .talabot-brand-pill>img[data-talabot-logo]{display:block;width:auto;height:44px;max-width:none;max-height:none;object-fit:contain;margin:0;padding:0;border-radius:0;background:transparent;box-sizing:content-box}
    .talabot-auth-pill{margin:0 auto 12px}
    #tlb-boot{background:#f6f6f8!important}
    #tlb-boot>.talabot-loading-pill{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);margin:0}
    #tlb-boot>.talabot-loading-pill+div{position:absolute;left:calc(50% - 22px);top:calc(50% + 54px);width:44px;height:44px;box-sizing:border-box}
    #tlb-boot>[data-i18n="loading"]{position:absolute;left:0;right:0;top:calc(50% + 112px);margin:0!important;padding:0 20px;text-align:center}
    /* Previous driver logo: 104px wide, original 2404x504 canvas. */
    .a-header .a-brand img{width:104px;height:21.8px;object-fit:contain;object-position:left}
    .talabot-side-pill{margin-bottom:8px}
    body.st-merchant .nav>.talabot-nav-pill{display:none}
    body.st-merchant .nav::before{content:none}
    @media(min-width:1024px){
      body.st-merchant .nav{padding-top:110px!important}
      body.st-merchant .nav>.talabot-nav-pill{display:inline-flex;position:absolute;left:22px;top:26px;margin:0}
    }
  `;
  document.head.append(style);
  window.TALABOT_BRAND = Object.freeze({source, html, pill, sync});

  // setLang updates both TLB listeners and the document language. Observe new
  // render/overlay nodes only; changing our own image attributes cannot loop.
  TLB.on(sync);
  new MutationObserver(sync).observe(document.documentElement, {attributes: true, attributeFilter: ['lang']});
  new MutationObserver(records => {
    if (records.some(record => record.addedNodes.length)) sync();
  }).observe(document.body, {childList: true, subtree: true});
  sync();
}());
