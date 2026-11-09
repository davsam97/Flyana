/* Runs before the app bundle, as a classic script written in ES5 so that any
   browser can parse it. The SPA needs the same floor as Tailwind CSS v4
   (Chrome/Edge 111, Firefox 128, Safari 16.4): below it the page would stay
   blank or unstyled, so a readable message replaces it instead. */
;(function () {
  var supported =
    typeof window.CSS !== 'undefined' &&
    typeof CSS.supports === 'function' &&
    CSS.supports('color', 'color-mix(in srgb, red, blue)') && // Firefox 113, Safari 16.2
    'CSSLayerBlockRule' in window && // @layer: Safari 15.4
    'CSSPropertyRule' in window && // @property: Firefox 128, Safari 16.4
    'noModule' in document.createElement('script') &&
    typeof Array.prototype.at === 'function' &&
    typeof window.structuredClone === 'function'
  if (supported) return

  var messages = {
    fr: {
      title: 'Navigateur non pris en charge',
      body: 'Flyana a besoin d’une version récente de Firefox (128+), Chrome ou Edge (111+), ou Safari (16.4+). Mettez votre navigateur à jour puis rechargez la page.',
    },
    en: {
      title: 'Unsupported browser',
      body: 'Flyana needs a recent version of Firefox (128+), Chrome or Edge (111+), or Safari (16.4+). Please update your browser and reload the page.',
    },
  }
  var cookie = /(?:^|;\s*)flyana_locale=(\w+)/.exec(document.cookie)
  var lang = (cookie ? cookie[1] : navigator.language || 'fr').slice(0, 2)
  var text = messages[lang] || messages.fr

  function render() {
    var box = document.createElement('div')
    box.setAttribute('role', 'alert')
    box.style.cssText =
      'max-width:32rem;margin:15vh auto;padding:2rem;border-radius:14px;' +
      'font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;' +
      'background:#13161d;color:#f7f8fc;border:1px solid #5f6575'
    var title = document.createElement('h1')
    title.style.cssText = 'margin:0 0 .75rem;font-size:1.375rem'
    title.appendChild(document.createTextNode(text.title))
    var body = document.createElement('p')
    body.style.margin = '0'
    body.appendChild(document.createTextNode(text.body))
    box.appendChild(title)
    box.appendChild(body)
    document.body.innerHTML = ''
    document.body.style.cssText = 'margin:0;padding:0 1rem;background:#0a0d13'
    document.body.appendChild(box)
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render)
  else render()
})()
