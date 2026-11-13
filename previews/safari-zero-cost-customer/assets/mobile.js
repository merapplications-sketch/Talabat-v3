/* Browser chrome/keyboard adaptation; never modifies the user's zoom. */
(function(){'use strict';
 function update(){var v=window.visualViewport,a=document.activeElement,editing=a&&/^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)&&!/^(checkbox|radio|button|submit|file)$/.test(a.type||'');if(v&&v.scale!==1)return;var h=v?v.height:innerHeight,inset=v?Math.max(0,innerHeight-v.height-v.offsetTop):0;document.documentElement.style.setProperty('--tlb-visible-height',h+'px');document.documentElement.style.setProperty('--tlb-keyboard-inset',inset+'px');document.body.classList.toggle('tlb-keyboard',!!editing&&inset>120)}
 document.addEventListener('focusin',update);document.addEventListener('focusout',function(){requestAnimationFrame(update)});window.addEventListener('resize',update);if(window.visualViewport){visualViewport.addEventListener('resize',update);visualViewport.addEventListener('scroll',update)}update();
})();
