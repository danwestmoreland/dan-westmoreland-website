/* danwestmoreland.com shared script.
 * Edit the three values in SITE_CONFIG after you create the accounts.
 * Anything left blank is simply skipped, so the site works before setup.
 */
var SITE_CONFIG = {
  // Cal.com booking link, the part after cal.com/ (e.g. "danwestmoreland/30min").
  calLink: "",
  // HubSpot free CRM portal ID (Settings > Account defaults). Loads the free
  // tracking code, which logs page views and auto-captures the Netlify form.
  hubspotPortalId: "",
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
    window.Cal.ns.dw("ui", { hideEventTypeDetails: false, layout: "month_view", cssVarsPerTheme: { light: { "cal-brand": "#D9512C" } } });
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
