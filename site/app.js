(function () {
  "use strict";

  var DEFAULT_TAB = "alien";

  /* Words in a listing title that tell which version of a figure it is. Used for the filter chips. */
  var VERSIONS = [
    { id: "ultimate", label: "Ultimate", re: /\bultimate\b/ },
    { id: "quarter", label: "1/4 scale (18 inch)", re: /\b1 ?\/ ?4\b|\b1 ?: ?4\b|quarter scale|\b18 ?("|”|inch|in\b)/ },
    { id: "kenner", label: "Kenner Tribute", re: /\bkenner\b/ },
    { id: "deluxe", label: "Deluxe", re: /\bdeluxe\b/ },
    { id: "clothed", label: "Clothed or retro", re: /\bclothed\b|\bretro\b/ },
    { id: "exclusive", label: "Exclusive", re: /exclusive|\bsdcc\b|\bnycc\b|comic.?con|convention|toys ?r ?us|\btru\b|\btarget\b|walmart|gamestop|loot ?crate/ },
    { id: "battle", label: "Battle damaged", re: /battle.?damage/ },
    { id: "glow", label: "Glow in the dark", re: /\bglow|\bgitd\b/ },
    { id: "signed", label: "Signed", re: /\bsigned\b|autograph/ }
  ];

  function el(id) { return document.getElementById(id); }

  function esc(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function safeUrl(url) {
    return typeof url === "string" && url.indexOf("https://") === 0 ? url : "";
  }

  function dollars(n) {
    return "$" + Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function total(item) { return item.price + (item.shipping || 0); }

  function timeAgo(iso) {
    var mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return mins + (mins === 1 ? " minute ago" : " minutes ago");
    var hrs = Math.round(mins / 60);
    if (hrs < 48) return hrs + (hrs === 1 ? " hour ago" : " hours ago");
    return Math.round(hrs / 24) + " days ago";
  }

  function timeLeft(iso) {
    var ms = new Date(iso).getTime() - Date.now();
    if (ms <= 0) return null;
    var mins = Math.floor(ms / 60000);
    var d = Math.floor(mins / 1440), h = Math.floor((mins % 1440) / 60), m = mins % 60;
    if (d > 0) return d + "d " + h + "h left";
    if (h > 0) return h + "h " + m + "m left";
    return m + "m left";
  }

  function stillOpen(item) {
    return item.kind !== "Auction" || !item.ends || new Date(item.ends).getTime() > Date.now();
  }

  function loadJson(path) {
    return fetch(path + "?t=" + Date.now(), { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error(path + " returned " + r.status);
      return r.json();
    });
  }

  function initials(name) {
    return String(name).replace(/\(.*?\)/g, "").split(/\s+/).filter(Boolean).slice(0, 2)
      .map(function (w) { return w.charAt(0); }).join("").toUpperCase();
  }

  function thumbHtml(url, alt, label) {
    var safe = safeUrl(url);
    return safe
      ? '<img src="' + esc(safe) + '" alt="' + esc(alt) + '" loading="lazy" referrerpolicy="no-referrer">'
      : '<span class="ph">' + esc(label) + "</span>";
  }

  function params() { return new URLSearchParams(location.search); }

  function tabInfo(catalog, id) {
    var t = null;
    catalog.tabs.forEach(function (x) { if (x.id === id) t = x; });
    return t;
  }

  function setTheme(tab) {
    document.body.setAttribute("data-theme", tab.id);
  }

  function renderTabs(catalog, current) {
    el("tabs").innerHTML = '<a class="brand" href="index.html?tab=' + esc(current) + '">NECA Finder</a><div class="tab-row">' +
      catalog.tabs.map(function (t) {
        return '<a class="tab tab-' + esc(t.id) + '" href="index.html?tab=' + esc(t.id) + '"' +
          (t.id === current ? ' aria-current="page"' : "") + ">" + esc(t.name) + "</a>";
      }).join("") + "</div>";
  }

  function figureSummary(fig, data) {
    var entry = data.figures[fig.id];
    var items = (entry && entry.listings ? entry.listings : []).filter(stillOpen);
    var lowest = null, store = null, image = null;
    items.forEach(function (it) {
      if (lowest === null || total(it) < lowest) lowest = total(it);
      if (it.source === "neca" && !store) store = it;
    });
    if (store) image = safeUrl(store.image);
    for (var i = 0; i < items.length && !image; i += 1) image = safeUrl(items[i].image);
    var official = safeUrl(data.images[fig.id]);
    var remembered = safeUrl(data.photos[fig.id]);
    return { items: items, lowest: lowest, store: store, image: official || image || remembered };
  }

  function showStatus(data, forSale, count) {
    var updated = el("updated");
    var bits = [];
    if (typeof forSale === "number") bits.push(forSale + " of " + count + " figures have sealed copies for sale.");
    bits.push(data.updated ? "Listings updated " + timeAgo(data.updated) + ", and they refresh about every hour." : "Waiting for the first update.");
    updated.textContent = bits.join(" ");

    var html = "";
    if (data.status === "waiting") {
      html = '<div class="banner"><strong>The first update has not finished yet.</strong> Check back in a few minutes. If this stays for more than an hour, see "Fixing problems" in the setup guide.</div>';
    } else if (data.status === "needs_keys") {
      html = '<div class="banner"><strong>The eBay keys are missing.</strong> Only NECA store listings show until EBAY_CLIENT_ID and EBAY_CLIENT_SECRET are added in the GitHub repository settings.</div>';
    } else if (data.status === "bad_keys") {
      html = '<div class="banner bad"><strong>eBay did not accept the keys.</strong> Copy the Production App ID and Cert ID from the eBay developer site again and paste them into the GitHub secrets.</div>';
    } else if (data.updated && Date.now() - new Date(data.updated).getTime() > 4 * 3600 * 1000) {
      html = '<div class="banner"><strong>These listings are more than 4 hours old.</strong> The hourly update may be paused, so some of these could already be sold.</div>';
    }
    el("banner").innerHTML = html;

    var rules = data.rules || {};
    if (rules.min_seller_positive_percent != null) {
      el("foot").textContent =
        "eBay listings shown are marked New, come from " + (rules.us_sellers_only ? "US " : "") + "sellers with at least " +
        rules.min_seller_positive_percent + "% positive feedback and " + rules.min_seller_ratings +
        " ratings, and have titles that say NECA or Reel Toys. Titles that mention opened, loose, used, custom, bundled or fake items are hidden." +
        (rules.neca_store ? " NECA store listings come straight from store.necaonline.com." : "") +
        (rules.shipping_for_zip ? " Shipping prices are what eBay quotes for delivery to your ZIP code." : "") +
        " Always read the listing and look at the photos before you buy.";
    }
  }

  /* ===== Home page: one tab ===== */

  function renderHome(catalog, data) {
    var tabId = params().get("tab");
    var tab = tabInfo(catalog, tabId) || tabInfo(catalog, DEFAULT_TAB);
    setTheme(tab);
    renderTabs(catalog, tab.id);
    document.title = tab.name + " | NECA Finder";
    el("title").textContent = tab.title;
    el("tagline").textContent = tab.tagline;

    var figs = catalog.figures.filter(function (f) { return f.tabs.indexOf(tab.id) !== -1; });
    var rows = figs.map(function (f) { return { f: f, sum: figureSummary(f, data) }; })
      .filter(function (r) { return !r.f.other || r.sum.items.length > 0; });
    var forSale = rows.filter(function (r) { return r.sum.items.length > 0; }).length;
    showStatus(data, forSale, rows.length);

    var q = el("q"), only = el("onlyForSale");

    function draw() {
      var term = q.value.trim().toLowerCase();
      var html = tab.sections.map(function (section) {
        var list = rows.filter(function (r) {
          if (r.f.section !== section) return false;
          if (only.checked && r.sum.items.length === 0) return false;
          if (term && r.f.name.toLowerCase().indexOf(term) === -1 &&
              !r.sum.items.some(function (it) { return it.title.toLowerCase().indexOf(term) !== -1; })) return false;
          return true;
        });
        if (!list.length) return "";
        var n = list.filter(function (r) { return r.sum.items.length > 0; }).length;
        return '<section class="section"><div class="section-head"><h2>' + esc(section) + '</h2><p class="count">' +
          n + " of " + list.length + " for sale</p></div>" +
          '<div class="grid">' + list.map(function (r) { return tileHtml(r, tab); }).join("") + "</div></section>";
      }).join("");
      el("sections").innerHTML = html || '<p class="empty">Nothing matches. Clear the search box or untick "Only show figures for sale".</p>';
    }

    q.addEventListener("input", draw);
    only.addEventListener("change", draw);
    draw();
  }

  function tileHtml(row, tab) {
    var f = row.f, sum = row.sum;
    var sale = sum.items.length === 0
      ? '<span class="sale none">None for sale right now</span>'
      : '<span class="sale">' + sum.items.length + " for sale, from " + dollars(sum.lowest) + "</span>";
    var badge = sum.store ? '<span class="badge">' + (sum.store.preorder ? "Pre-order at NECA" : "In stock at NECA") + "</span>" : "";
    return '<a class="tile' + (sum.items.length ? "" : " empty-tile") + '" href="figure.html?f=' + encodeURIComponent(f.id) + "&tab=" + encodeURIComponent(tab.id) + '">' +
      '<div class="thumb" data-label="' + esc(initials(f.name)) + '">' + thumbHtml(sum.image, f.name, initials(f.name)) + badge + "</div>" +
      '<div class="body"><h3>' + esc(f.name) + "</h3>" + sale + "</div></a>";
  }

  /* ===== Figure page ===== */

  function renderFigure(catalog, data) {
    var p = params();
    var fig = null;
    catalog.figures.forEach(function (f) { if (f.id === p.get("f")) fig = f; });
    var tab = tabInfo(catalog, p.get("tab"));
    if (fig && (!tab || fig.tabs.indexOf(tab.id) === -1)) tab = tabInfo(catalog, fig.tabs[0]);
    if (!tab) tab = tabInfo(catalog, DEFAULT_TAB);
    setTheme(tab);
    renderTabs(catalog, tab.id);
    el("back").href = "index.html?tab=" + encodeURIComponent(tab.id);
    el("back").textContent = "Back to all " + tab.name + " figures";
    showStatus(data);

    if (!fig) {
      el("figHero").innerHTML = '<div><h1>Figure not found</h1><p>Go back to the list and pick a figure.</p></div>';
      return;
    }
    document.title = fig.name + " | NECA Finder";
    var sum = figureSummary(fig, data);

    var facts = "<li><span>Line</span><b>" + esc(tab.title) + "</b></li>" +
      "<li><span>Group</span><b>" + esc(fig.section) + "</b></li>" +
      "<li><span>Sealed for sale</span><b>" + sum.items.length + "</b></li>" +
      (sum.lowest !== null ? "<li><span>Lowest total</span><b>" + dollars(sum.lowest) + "</b></li>" : "") +
      (sum.store ? "<li><span>NECA store</span><b>" + (sum.store.preorder ? "Pre-order " : "In stock ") + dollars(sum.store.price) + "</b></li>" : "");
    el("figHero").innerHTML =
      '<div class="thumb big" data-label="' + esc(initials(fig.name)) + '">' + thumbHtml(sum.image, fig.name, initials(fig.name)) + "</div>" +
      "<div><h1>" + esc(fig.name) + '</h1><ul class="facts">' + facts + "</ul>" +
      (fig.other ? "" : '<p class="elsewhere"><a class="amazon" href="' + esc(amazonUrl(fig, tab)) + '" target="_blank" rel="noopener noreferrer">Check Amazon for this figure</a>' +
        '<span>Opens an Amazon search. Look for "Ships from and sold by Amazon" or NECA\'s own store, and check the seller rating there.</span></p>') +
      (fig.other ? '<p class="note">These listings passed every check but did not match a named figure, so they are grouped here. Read titles closely.</p>' : "") +
      "</div>";

    var show = "all", version = "all";
    var sortSel = el("sort");
    var withVersions = sum.items.map(function (it) {
      var t = it.title.toLowerCase();
      return { it: it, v: VERSIONS.filter(function (v) { return v.re.test(t); }).map(function (v) { return v.id; }) };
    });

    function drawChips() {
      var counts = {};
      withVersions.forEach(function (x) { x.v.forEach(function (id) { counts[id] = (counts[id] || 0) + 1; }); });
      var used = VERSIONS.filter(function (v) { return counts[v.id]; });
      if (used.length === 0 || sum.items.length < 2) { el("chips").innerHTML = ""; return; }
      el("chips").innerHTML = '<button type="button" class="chip" data-v="all" aria-pressed="' + (version === "all") + '">All versions</button>' +
        used.map(function (v) {
          return '<button type="button" class="chip" data-v="' + v.id + '" aria-pressed="' + (version === v.id) + '">' + esc(v.label) + " (" + counts[v.id] + ")</button>";
        }).join("");
      Array.prototype.forEach.call(el("chips").querySelectorAll("button"), function (b) {
        b.addEventListener("click", function () { version = b.getAttribute("data-v"); drawChips(); draw(); });
      });
    }

    function draw() {
      var items = withVersions.filter(function (x) {
        return (show === "all" || x.it.kind === show) && (version === "all" || x.v.indexOf(version) !== -1);
      }).map(function (x) { return x.it; });
      var mode = sortSel.value;
      items.sort(function (a, b) {
        if (mode === "high") return total(b) - total(a);
        if (mode === "ending") {
          var ae = a.ends ? new Date(a.ends).getTime() : Infinity;
          var be = b.ends ? new Date(b.ends).getTime() : Infinity;
          return ae === be ? total(a) - total(b) : ae - be;
        }
        if (mode === "newest") {
          return (b.listed ? new Date(b.listed).getTime() : 0) - (a.listed ? new Date(a.listed).getTime() : 0);
        }
        return total(a) - total(b);
      });
      if (sum.items.length === 0) {
        el("list").innerHTML = '<p class="empty">No sealed copies from trusted sellers are listed right now. This page checks again every hour.</p>';
        return;
      }
      if (items.length === 0) {
        el("list").innerHTML = '<p class="empty">None match these filters. Pick "All" and "All versions" to see every listing.</p>';
        return;
      }
      el("list").innerHTML = items.map(function (it) { return itemHtml(it, fig); }).join("");
    }

    el("filters").hidden = sum.items.length === 0;
    Array.prototype.forEach.call(document.querySelectorAll(".seg button"), function (btn) {
      btn.addEventListener("click", function () {
        show = btn.getAttribute("data-show");
        Array.prototype.forEach.call(document.querySelectorAll(".seg button"), function (b) {
          b.setAttribute("aria-pressed", b === btn ? "true" : "false");
        });
        draw();
      });
    });
    sortSel.addEventListener("change", draw);
    drawChips();
    draw();
  }

  /* Amazon has no free listings feed, so each figure links to an Amazon search for it instead */
  function amazonUrl(fig, tab) {
    var name = fig.name.replace(/\((all versions|version not in title)\)/gi, "").replace(/\band more\b|\bgame figures\b|\bfigures\b/gi, "").replace(/[(),:]/g, " ");
    var words = name.toLowerCase();
    var line = { alien: "Alien", predator: "Predator", robocop: "RoboCop", terminator: "Terminator", thing: "The Thing", efny: "Escape From New York" }[tab.id] || "";
    if (line && words.indexOf(line.toLowerCase().split(" ").pop()) === -1) name = line + " " + name;
    return "https://www.amazon.com/s?k=" + encodeURIComponent(("NECA " + name).replace(/\s+/g, " ").trim()) + "&i=toys-and-games";
  }

  function itemHtml(it, fig) {
    var tags = [];
    var isStore = it.source === "neca";
    if (isStore) {
      tags.push('<span class="tag store">' + (it.preorder ? "NECA store pre-order" : "In stock at the NECA store") + "</span>");
    } else if (it.kind === "Auction") {
      var left = it.ends ? timeLeft(it.ends) : null;
      tags.push('<span class="tag auction">Auction, ' + it.bids + (it.bids === 1 ? " bid" : " bids") + (left ? ", " + left : "") + "</span>");
    } else {
      tags.push('<span class="tag">Buy It Now' + (it.best_offer ? " or Best Offer" : "") + "</span>");
    }
    if (it.box_note) tags.push('<span class="tag warn">Box damage mentioned</span>');
    if (!isStore && it.listed && Date.now() - new Date(it.listed).getTime() < 48 * 3600 * 1000) tags.push('<span class="tag">Listed in the last 2 days</span>');

    var ship;
    if (isStore) ship = "Shipping shown at NECA checkout";
    else if (it.shipping === null || it.shipping === undefined) ship = "Shipping shown at checkout";
    else if (it.shipping === 0) ship = "Free shipping";
    else ship = "plus " + dollars(it.shipping) + " shipping";

    var seller = isStore
      ? '<div class="seller">Sold by NECA</div>'
      : (it.seller_percent != null
        ? '<div class="seller">Seller: ' + esc(it.seller_percent) + "% positive from " + Number(it.seller_ratings).toLocaleString("en-US") + " ratings</div>"
        : "");

    return '<article class="item' + (isStore ? " from-store" : "") + '">' +
      '<div class="thumb" data-label="' + esc(initials(fig.name)) + '">' + thumbHtml(it.image, it.title, initials(fig.name)) + "</div>" +
      "<div><h3>" + esc(it.title) + "</h3>" +
      '<div class="tags">' + tags.join("") + "</div>" + seller + "</div>" +
      '<div class="price"><div class="big">' + dollars(it.price) + "</div>" +
      '<div class="ship">' + ship + "</div>" +
      '<a class="buy" href="' + esc(safeUrl(it.url)) + '" target="_blank" rel="noopener noreferrer">' + (isStore ? "View on NECA store" : "View on eBay") + "</a></div>" +
      "</article>";
  }

  /* If a photo cannot load, show the figure's initials instead of a broken image */
  document.addEventListener("error", function (e) {
    var img = e.target;
    if (img && img.tagName === "IMG" && img.parentNode && img.parentNode.classList.contains("thumb")) {
      var box = img.parentNode;
      var label = document.createElement("span");
      label.className = "ph";
      label.textContent = box.getAttribute("data-label") || "";
      box.replaceChild(label, img);
    }
  }, true);

  /* ===== Start ===== */

  Promise.all([loadJson("data/catalog.json"), loadJson("data/listings.json")])
    .then(function (res) {
      var catalog = res[0], data = res[1];
      data.figures = data.figures || {};
      data.images = data.images || {};
      data.photos = data.photos || {};
      if (document.body.getAttribute("data-page") === "figure") renderFigure(catalog, data);
      else renderHome(catalog, data);
    })
    .catch(function (err) {
      el("banner").innerHTML = '<div class="banner bad"><strong>The page could not load its data.</strong> Refresh the page. If this keeps happening, see "Fixing problems" in the setup guide.</div>';
      el("updated").textContent = "";
      if (window.console) console.error(err);
    });
})();
