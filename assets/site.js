/* danwestmoreland.com shared script.
 * Edit the three values in SITE_CONFIG after you create the accounts.
 * Anything left blank is simply skipped, so the site works before setup.
 */
var SITE_CONFIG = {
  // Cal.com booking link, the part after cal.com/ (e.g. "danwestmoreland/30min").
  calLink: "dan-westmoreland/call",
  // HubSpot free CRM portal ID (Settings > Account defaults). Loads the free
  // tracking code, which logs page views and auto-captures the Netlify form.
  hubspotPortalId: "247629889",
  // Microsoft Clarity project ID (free heatmaps and session recordings). Optional.
  clarityId: ""
};

(function () {
  var params = new URLSearchParams(window.location.search);
  var KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "company", "seg"];

  // 1. Persist attribution for the session so it survives clicking to /book/.
  var attrib = {};
  try { attrib = JSON.parse(sessionStorage.getItem("dw_attrib") || "{}"); } catch (e) { attrib = {}; }
  KEYS.forEach(function (k) {
    var v = params.get(k);
    if (v) attrib[k] = v.slice(0, 120);
  });
  if (!attrib.landing_page) attrib.landing_page = window.location.pathname;
  try { sessionStorage.setItem("dw_attrib", JSON.stringify(attrib)); } catch (e) {}

  // 2. Fill hidden attribution fields on any form.
  document.querySelectorAll("form [data-attrib]").forEach(function (input) {
    var k = input.getAttribute("data-attrib");
    if (attrib[k]) input.value = attrib[k];
  });

  // 2b. Preselect the matching offer in the booking form's "need" dropdown.
  var needSel = document.getElementById("f-need");
  if (needSel && attrib.seg) {
    for (var i = 0; i < needSel.options.length; i++) {
      if (needSel.options[i].value === attrib.seg) { needSel.selectedIndex = i; break; }
    }
  }

  // 3. Personalize outbound landing pages: ?company=Acme shows "Prepared for Acme".
  var company = attrib.company;
  if (company) {
    document.querySelectorAll("[data-company]").forEach(function (el) {
      el.textContent = company;
    });
    document.querySelectorAll(".for-banner").forEach(function (el) { el.classList.add("on"); });
  }

  // 4. Carry attribution onto booking links.
  document.querySelectorAll('a[href^="/book"]').forEach(function (a) {
    var parts = a.getAttribute("href").split("?");
    var qs = new URLSearchParams(parts[1] || "");
    KEYS.forEach(function (k) { if (attrib[k] && !qs.get(k)) qs.set(k, attrib[k]); });
    var s = qs.toString();
    if (s) a.setAttribute("href", a.getAttribute("href").split("?")[0] + "?" + s);
  });

  // 5. Cal.com inline embed on /book/.
  var calEl = document.getElementById("cal-inline");
  if (calEl && SITE_CONFIG.calLink) {
    calEl.innerHTML = "";
    (function (C, A, L) {
      var p = function (a, ar) { a.q.push(ar); };
      var d = C.document;
      C.Cal = C.Cal || function () {
        var cal = C.Cal; var ar = arguments;
        if (!cal.loaded) { cal.ns = {}; cal.q = cal.q || []; d.head.appendChild(d.createElement("script")).src = A; cal.loaded = true; }
        if (ar[0] === L) {
          var api = function () { p(api, arguments); };
          var namespace = ar[1]; api.q = api.q || [];
          if (typeof namespace === "string") { cal.ns[namespace] = cal.ns[namespace] || api; p(cal.ns[namespace], ar); p(cal, ["initNamespace", namespace]); }
          else p(cal, ar);
          return;
        }
        p(cal, ar);
      };
    })(window, "https://app.cal.com/embed/embed.js", "init");
    window.Cal("init", "dw", { origin: "https://cal.com" });
    window.Cal.ns.dw("inline", {
      elementOrSelector: "#cal-inline",
      calLink: SITE_CONFIG.calLink,
      config: { layout: "month_view", theme: "light" }
    });
    window.Cal.ns.dw("ui", { hideEventTypeDetails: false, layout: "month_view", cssVarsPerTheme: { light: { "cal-brand": "#B8431F" } } });
  }

  // 6. HubSpot free tracking code.
  if (SITE_CONFIG.hubspotPortalId) {
    var hs = document.createElement("script");
    hs.id = "hs-script-loader"; hs.async = true; hs.defer = true;
    hs.src = "https://js.hs-scripts.com/" + encodeURIComponent(SITE_CONFIG.hubspotPortalId) + ".js";
    document.head.appendChild(hs);
  }

  // 7. Microsoft Clarity.
  if (SITE_CONFIG.clarityId) {
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i;
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
    })(window, document, "clarity", "script", SITE_CONFIG.clarityId);
  }

  var yr = document.getElementById("year");
  if (yr) yr.textContent = new Date().getFullYear();
})();

/* Motion: inject gutter orbs and hero orbs, reveal sections on scroll with stagger, count-up numbers, highlight accent phrases. Homepage has its own markup, so skip there. */
(function(){
  document.documentElement.classList.add('js');
  if (document.querySelector('.gutter-orbs')) return;
  var layer = document.createElement('div'); layer.className = 'gutter-orbs'; layer.setAttribute('aria-hidden', 'true');
  layer.innerHTML = '<div class="gorb o gL g1"></div><div class="gorb g gL g2"></div><div class="gorb p gL g3"></div><div class="gorb g gR g4"></div><div class="gorb o gR g5"></div><div class="gorb p gR g6"></div>';
  document.body.insertBefore(layer, document.body.firstChild);
  var hero = document.querySelector('.page-hero');
  if (hero && !hero.querySelector('.orbs')) { var o = document.createElement('div'); o.className = 'orbs'; o.setAttribute('aria-hidden', 'true'); o.innerHTML = '<div class="orb o o1"></div><div class="orb g o2"></div>'; hero.insertBefore(o, hero.firstChild); }
  /* Accent phrases that get the highlight sweep */
  document.querySelectorAll('.page-hero h1 em, .band h2 em, .section-title em, .play-article > p:first-of-type strong, .lede strong').forEach(function(el){ el.classList.add('hl'); });
  var targets = document.querySelectorAll('main > section > *:not(.orbs), .card, .play-item, .talk, .tier, .step, .faq-item, .stat, .check-list li, .compare tbody tr, .band-inner > *');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!('IntersectionObserver' in window) || reduce) return;
  function countUp(el){
    if (el.dataset.counted) return; el.dataset.counted = '1';
    var m = /^([^\d]*)([\d,]*\.?\d+)(.*)$/.exec(el.textContent.trim()); if (!m) return;
    var pre = m[1], num = m[2], post = m[3]; var dec = (num.split('.')[1] || '').length; var comma = num.indexOf(',') > -1;
    var end = parseFloat(num.replace(/,/g, '')); if (isNaN(end)) return;
    var t0 = null, dur = 1100;
    function fmt(v){ var s = v.toFixed(dec); if (comma) s = s.replace(/\B(?=(\d{3})+(?!\d))/g, ','); return pre + s + post; }
    function step(ts){ if (!t0) t0 = ts; var p = Math.min(1, (ts - t0) / dur); var e = 1 - Math.pow(1 - p, 3); el.textContent = fmt(end * e); if (p < 1) requestAnimationFrame(step); else el.textContent = fmt(end); }
    requestAnimationFrame(step);
  }
  var io = new IntersectionObserver(function(entries){ entries.forEach(function(en){ if (en.isIntersecting) { var el = en.target; el.classList.add('in'); io.unobserve(el); el.querySelectorAll('.stat-num').forEach(countUp); if (el.classList.contains('stat-num')) countUp(el); } }); }, { threshold: 0.05 });
  targets.forEach(function(el){
    if (el.closest('.site-header')) return;
    el.classList.add('rv');
    var sib = el.parentNode ? Array.prototype.filter.call(el.parentNode.children, function(c){ return c.matches('.card, .play-item, .talk, .tier, .step, .faq-item, .stat, li, tr'); }) : [];
    var i = sib.indexOf(el); if (i > 0) el.style.setProperty('--i', Math.min(i, 8));
    io.observe(el);
  });
})();

/* RB2B website visitor identification (production only). Key: 7N850HKY28N1 */
(function(key){
  if (location.hostname !== 'danwestmoreland.com' && location.hostname !== 'www.danwestmoreland.com') return;
  if (window.reb2b) return;
  window.reb2b = {loaded: true};
  var s = document.createElement('script'); s.async = true;
  s.src = 'https://ddwl4m2hdecbv.cloudfront.net/b/' + key + '/' + key + '.js.gz';
  var f = document.getElementsByTagName('script')[0]; f.parentNode.insertBefore(s, f);
})('7N850HKY28N1');
