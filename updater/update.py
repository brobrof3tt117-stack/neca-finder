#!/usr/bin/env python3
"""
NECA Finder: hourly updater.

GitHub runs this file automatically every hour. You never need to run it yourself.
It asks eBay's official Browse API for new, sealed NECA figures from the Alien,
Predator, RoboCop, Terminator, The Thing and Escape From New York lines, keeps only
trustworthy sellers, adds anything in stock or on pre-order at the official NECA
store, and saves the results to site/data/listings.json for the website.

Settings you might want to change live in updater/settings.json.
The list of figures lives in tools/build_catalog.py (which writes site/data/catalog.json).
"""

import base64
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parent.parent
CATALOG_FILE = ROOT / "site" / "data" / "catalog.json"
OUT_FILE = ROOT / "site" / "data" / "listings.json"
SETTINGS_FILE = ROOT / "updater" / "settings.json"
HEARTBEAT_FILE = ROOT / "updater" / "last-run-day.txt"
SHIPPING_FILE = ROOT / "updater" / "shipping-cache.json"
IMAGES_FILE = ROOT / "updater" / "figure-images.json"
PHOTOS_FILE = ROOT / "updater" / "listing-photos.json"

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
ITEM_URL = "https://api.ebay.com/buy/browse/v1/item/"
SCOPE = "https://api.ebay.com/oauth/api_scope"
MARKETPLACE = "EBAY_US"
CONDITION_NEW = "1000"  # eBay's code for "New": brand new, unopened, in the original package
PAGE_SIZE = 200
MAX_PAGES = 10        # up to 2,000 results per search
BATCH_SIZE = 20       # eBay's most listings per batch lookup
MAX_BATCH_CALLS = 15  # up to 300 listings priced per update
TIMEOUT = 30

# A handful of broad searches cover all six lines. Each listing is then matched to its figure here.
# eBay requires every word in a search, so these stay short.
SEARCHES = [
    "neca alien", "neca aliens", "neca xenomorph",
    "neca predator", "neca prey predator", "neca avp",
    "neca robocop", "neca terminator",
    "neca thing macready", "neca the thing",
    "neca plissken", "neca escape from new york",
]

NECA_STORE = "https://store.necaonline.com"
NECA_HEADERS = {"User-Agent": "NecaFinder/1.0 (personal hobby site; reads the public product list once an hour)"}
NECA_FIGURE_TYPES = {"figure", "ultramate", "action figure"}


class AuthError(Exception):
    """eBay rejected the keys. Retrying will not help."""


class TemporaryError(Exception):
    """eBay or the network had a hiccup. Worth trying again next hour."""


class NotAllowed(TemporaryError):
    """eBay says these keys may not use this particular feature."""


# ===== text helpers =====

SPELLINGS = [
    (r"\bt(\d{3,4})\b", r"t \1"),                 # t800 -> t 800
    (r"\bed(\d{3})\b", r"ed \1"),                 # ed209 -> ed 209
    (r"\bjudgement\b", "judgment"),
    (r"\bmc ?ready\b", "macready"),
    (r"\bmcreedy\b", "macready"),
    (r"\bplis+k[ie]n\b", "plissken"),
    (r"\bplisken\b", "plissken"),
    (r"\brobo cop\b", "robocop"),
    (r"\bversus\b", "vs"),
    (r"\bface hugger\b", "facehugger"),
    (r"\bendo skeleton\b", "endoskeleton"),
    (r"\bxenomorphs\b", "xenomorph"),
    (r"\bterminter\b|\btermintor\b|\bterminater\b", "terminator"),
    (r"\bnew york city\b", "new york"),
]
SPELLINGS = [(re.compile(a), b) for a, b in SPELLINGS]


def normalize(text):
    """Lowercase, '&' becomes 'and', every run of punctuation or spaces becomes one space,
    and common spelling differences are made the same."""
    text = (text or "").lower().replace("&", " and ")
    out = []
    prev_space = True
    for ch in text:
        if ch.isascii() and ch.isalnum():
            out.append(ch)
            prev_space = False
        elif not prev_space:
            out.append(" ")
            prev_space = True
    s = "".join(out).strip()
    for pattern, repl in SPELLINGS:
        s = pattern.sub(repl, s)
    return s


def padded(text):
    return f" {normalize(text)} "


def has(pad, phrase):
    p = normalize(phrase)
    return bool(p) and f" {p} " in pad


def matches_any(pad, alternatives):
    """alternatives is a list of lists. True if every phrase of at least one inner list is present."""
    return any(alt and all(has(pad, w) for w in alt) for alt in alternatives)


# ===== matching a title to a figure =====

def match_figure(title, catalog):
    """Returns the first catalog figure the title fits, or None if the title names no figure."""
    pad = padded(title)
    tabs_ok = {rule["tab"] for rule in catalog["tab_words"] if matches_any(pad, rule["match"])}
    for fig in catalog["figures"]:
        if fig.get("other"):
            continue
        if not tabs_ok.intersection(fig["tabs"]):
            continue  # the title never says which line it is from, so it cannot be this figure
        if fig["not"] and any(has(pad, n) for n in fig["not"]):
            continue
        if matches_any(pad, fig["match"]):
            return fig
    # No named figure: the title never says which figure it is, so it is left out rather
    # than dumped in a catch-all tile.
    return None


def load_catalog():
    catalog = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    catalog["by_id"] = {f["id"]: f for f in catalog["figures"]}
    return catalog


# ===== filters =====

def title_problem(title, settings, allow_maybe=False):
    """Return a short reason if the title suggests the item is NOT a sealed figure, else None."""
    pad = padded(title)
    for ok in settings["ok_phrases"]:
        p = normalize(ok)
        if p:
            pad = pad.replace(f" {p} ", " ")
    for word in settings["hide_words"]:
        if has(pad, word):
            return f"hide word: {word}"
    for pair in settings.get("hide_pairs", []):
        if pair and all(has(pad, w) for w in pair):
            return f"hide pair: {' + '.join(pair)}"
    if not allow_maybe:
        sealed = any(has(pad, w) for w in settings["sealed_words"])
        if not sealed:
            for word in settings["maybe_hide_words"]:
                if has(pad, word):
                    return f"maybe hide word: {word}"
    return None


def is_neca(title, settings):
    pad = padded(title)
    return any(has(pad, w) for w in settings["must_have_words"])


def mentions_box_damage(title, settings):
    pad = padded(title)
    for ok in settings["ok_phrases"]:
        p = normalize(ok)
        if p:
            pad = pad.replace(f" {p} ", " ")
    return any(has(pad, w) for w in settings["box_warning_words"])


def seller_ok(seller, settings):
    try:
        pct = float(seller.get("feedbackPercentage"))
        count = int(seller.get("feedbackScore"))
    except (TypeError, ValueError):
        return False, None, None  # no rating info, so we cannot call them reliable
    ok = pct >= float(settings["min_seller_positive_percent"]) and count >= int(settings["min_seller_ratings"])
    return ok, pct, count


def money(obj):
    try:
        return round(float(obj["value"]), 2), obj.get("currency", "USD")
    except (TypeError, KeyError, ValueError):
        return None, None


def shipping_cost(item):
    """Cheapest shipping cost, 0.0 for free, or None if eBay gave no price."""
    best = None
    for opt in item.get("shippingOptions") or []:
        value, _ = money(opt.get("shippingCost"))
        if value is not None and (best is None or value < best):
            best = value
    return best


def safe_url(url):
    return url if isinstance(url, str) and url.startswith("https://") else None


def to_listing(item, settings):
    """Turn one eBay search result into the small record the website shows."""
    options = item.get("buyingOptions") or []
    is_auction = "AUCTION" in options
    is_bin = "FIXED_PRICE" in options
    if is_auction and not settings["show_auctions"]:
        return None
    if is_bin and not is_auction and not settings["show_buy_it_now"]:
        return None
    if not is_auction and not is_bin:
        return None

    if is_auction:
        price, currency = money(item.get("currentBidPrice"))
        if price is None:
            price, currency = money(item.get("price"))
    else:
        price, currency = money(item.get("price"))
    if price is None or currency != "USD":
        return None

    url = safe_url(item.get("itemWebUrl"))
    if not url:
        return None
    image = safe_url((item.get("image") or {}).get("imageUrl"))
    if not image:
        thumbs = item.get("thumbnailImages") or []
        image = safe_url(thumbs[0].get("imageUrl")) if thumbs else None

    _, pct, count = seller_ok(item.get("seller") or {}, settings)
    bids = item.get("bidCount")
    return {
        "id": str(item.get("itemId", "")),
        "source": "ebay",
        "title": item.get("title", ""),
        "url": url,
        "image": image,
        "price": price,
        "shipping": shipping_cost(item),
        "kind": "Auction" if is_auction else "Buy It Now",
        "best_offer": "BEST_OFFER" in options,
        "bids": int(bids) if isinstance(bids, int) else (0 if is_auction else None),
        "ends": item.get("itemEndDate") if is_auction else None,
        "listed": item.get("itemCreationDate"),
        "seller_percent": pct,
        "seller_ratings": count,
        "box_note": mentions_box_damage(item.get("title", ""), settings),
    }


def keep_item(item, catalog, settings):
    """All the checks in one place. Returns (figure id, listing) or (None, None)."""
    if str(item.get("conditionId", "")) != CONDITION_NEW:
        return None, None
    if settings["us_sellers_only"] and (item.get("itemLocation") or {}).get("country") != "US":
        return None, None
    title = item.get("title", "")
    if not is_neca(title, settings):
        return None, None
    if title_problem(title, settings):
        return None, None
    ok, _, _ = seller_ok(item.get("seller") or {}, settings)
    if not ok:
        return None, None
    fig = match_figure(title, catalog)
    if not fig:
        return None, None
    listing = to_listing(item, settings)
    if not listing:
        return None, None
    return fig["id"], listing


# ===== eBay calls =====

class Ebay:
    def __init__(self, client_id, client_secret, session=None, sleep=time.sleep, zip_code=""):
        self.zip_code = zip_code if zip_code.isdigit() and len(zip_code) == 5 else ""
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = session or requests.Session()
        self.sleep = sleep
        self.token = None
        self.calls = 0

    def headers(self):
        h = {"Authorization": f"Bearer {self.token}", "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE}
        if self.zip_code:
            # Tells eBay where the buyer is, so shipping is priced for that ZIP.
            h["X-EBAY-C-ENDUSERCTX"] = f"contextualLocation=country%3DUS%2Czip%3D{self.zip_code}"
        return h

    def refresh_token(self):
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        last = "unknown problem"
        for attempt in range(4):
            try:
                r = self.session.post(
                    TOKEN_URL,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": f"Basic {auth}",
                    },
                    data={"grant_type": "client_credentials", "scope": SCOPE},
                    timeout=TIMEOUT,
                )
            except requests.RequestException as e:
                last = f"network error: {e}"
                self.sleep(2 * (attempt + 1))
                continue
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                return
            if r.status_code in (400, 401, 403):
                raise AuthError(f"eBay rejected the keys ({r.status_code}): {r.text[:300]}")
            last = f"eBay answered {r.status_code}"
            self.sleep(2 * (attempt + 1))
        raise TemporaryError(f"Could not get an eBay token: {last}")

    def get(self, url, params=None):
        if not self.token:
            self.refresh_token()
        refreshed = False
        last = "unknown problem"
        for attempt in range(4):
            self.calls += 1
            try:
                r = self.session.get(url, params=params, headers=self.headers(), timeout=TIMEOUT)
            except requests.RequestException as e:
                last = f"network error: {e}"
                self.sleep(2 * (attempt + 1))
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code == 401 and not refreshed:
                self.refresh_token()
                refreshed = True
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"eBay answered {r.status_code}"
                self.sleep(3 * (attempt + 1))
                continue
            if r.status_code == 403:
                raise NotAllowed(f"eBay answered 403: {r.text[:300]}")
            raise TemporaryError(f"eBay answered {r.status_code}: {r.text[:300]}")
        raise TemporaryError(last)

    def get_item(self, item_id):
        """Full details of one listing, including the real shipping price to the ZIP."""
        return self.get(ITEM_URL + quote(item_id, safe=""))

    def get_items(self, item_ids):
        """Full details of up to 20 listings in one call (eBay's batch lookup)."""
        data = self.get(ITEM_URL.rstrip("/"), {"item_ids": ",".join(item_ids)})
        return data.get("items") or []

    def search(self, q, settings):
        options = []
        if settings["show_buy_it_now"]:
            options.append("FIXED_PRICE")
        if settings["show_auctions"]:
            options.append("AUCTION")
        filters = [f"conditionIds:{{{CONDITION_NEW}}}", f"buyingOptions:{{{'|'.join(options)}}}"]
        if settings["us_sellers_only"]:
            filters += ["itemLocationCountry:US", "deliveryCountry:US"]
        params = {"q": q, "limit": str(PAGE_SIZE), "filter": ",".join(filters)}
        items = []
        data = self.get(SEARCH_URL, params)
        pages = 1
        while True:
            items.extend(data.get("itemSummaries") or [])
            nxt = data.get("next")
            if not nxt or pages >= MAX_PAGES:
                break
            data = self.get(nxt)
            pages += 1
        return items


def empty_by_figure(catalog):
    return {f["id"]: [] for f in catalog["figures"]}


def sort_listings(by_fig):
    for listings in by_fig.values():
        listings.sort(key=lambda x: (x.get("source") != "neca", x["price"] + (x["shipping"] or 0)))


def fetch_all(ebay, catalog, settings):
    """Run the broad searches and sort every good listing into its figure.
    Returns (listings by figure id, number of searches that worked)."""
    by_fig = empty_by_figure(catalog)
    seen = set()
    worked = 0
    for q in SEARCHES:
        try:
            items = ebay.search(q, settings)
        except TemporaryError as e:
            print(f"The search '{q}' failed this hour ({e})")
            continue
        worked += 1
        kept = 0
        for item in items:
            item_id = item.get("itemId")
            if not item_id or item_id in seen:
                continue
            seen.add(item_id)
            fid, listing = keep_item(item, catalog, settings)
            if listing:
                by_fig[fid].append(listing)
                kept += 1
        print(f"Search '{q}': {len(items)} results, {kept} new sealed listing(s) kept")
    sort_listings(by_fig)
    return by_fig, worked


# ===== the official NECA store =====

def neca_store_products(session):
    """Every product in NECA's public store list (Shopify's products.json)."""
    products = []
    for page in range(1, 21):
        r = session.get(f"{NECA_STORE}/products.json", params={"limit": "250", "page": str(page)},
                        headers=NECA_HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            raise TemporaryError(f"NECA store answered {r.status_code}")
        batch = r.json().get("products") or []
        products.extend(batch)
        if len(batch) < 250:
            break
    return products


def store_listing(product):
    """Turn one NECA store product into a listing, or None if it cannot be bought right now."""
    variants = [v for v in product.get("variants") or [] if v.get("available")]
    if not variants:
        return None
    prices = []
    for v in variants:
        try:
            prices.append(round(float(v.get("price")), 2))
        except (TypeError, ValueError):
            pass
    handle = str(product.get("handle", ""))
    if not prices or not re.fullmatch(r"[a-z0-9\-]+", handle):
        return None
    images = product.get("images") or []
    title = str(product.get("title", ""))
    tags = [str(t).lower() for t in product.get("tags") or []]
    preorder = "pre-order" in title.lower() or "preorder" in title.lower() or any("pre-order" in t or "preorder" in t for t in tags)
    return {
        "id": "neca-" + handle,
        "source": "neca",
        "title": title,
        "url": f"{NECA_STORE}/products/{handle}",
        "image": safe_url(images[0].get("src")) if images else None,
        "price": min(prices),
        "shipping": None,
        "kind": "NECA Store",
        "preorder": preorder,
        "best_offer": False,
        "bids": None,
        "ends": None,
        "listed": product.get("published_at") or product.get("created_at"),
        "seller_percent": None,
        "seller_ratings": None,
        "box_note": False,
    }


def add_neca_store(by_fig, catalog, settings, session=None):
    """Adds NECA store figures that are in stock or on pre-order, and returns official pictures
    for any figure the store has (even sold out ones). Never stops the eBay update."""
    session = session or requests.Session()
    pictures = {}
    try:
        products = neca_store_products(session)
    except (requests.RequestException, ValueError, TemporaryError) as e:
        print(f"NECA store could not be read this time ({e})")
        return pictures, False
    added = 0
    for p in products:
        ptype = str(p.get("product_type", "")).strip().lower()
        title = str(p.get("title", ""))
        if ptype not in NECA_FIGURE_TYPES:
            continue
        if title_problem(title, settings, allow_maybe=True):
            continue
        fig = match_figure(title, catalog)
        if not fig:
            continue
        images = p.get("images") or []
        pic = safe_url(images[0].get("src")) if images else None
        if pic and not fig.get("other") and fig["id"] not in pictures:
            pictures[fig["id"]] = pic
        if settings.get("show_neca_store", True):
            listing = store_listing(p)
            if listing:
                by_fig[fig["id"]].append(listing)
                added += 1
    print(f"NECA store: {len(products)} products read, {added} matching figure(s) for sale.")
    sort_listings(by_fig)
    return pictures, True


def update_images(new_pictures):
    """Remembers official NECA pictures forever, so a figure keeps its picture after NECA sells out."""
    try:
        cache = json.loads(IMAGES_FILE.read_text(encoding="utf-8"))
        if not isinstance(cache, dict):
            cache = {}
    except (OSError, ValueError):
        cache = {}
    changed = False
    for fid, url in new_pictures.items():
        if fid not in cache:
            cache[fid] = url
            changed = True
    if changed:
        IMAGES_FILE.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return cache


def update_photos(by_fig, catalog):
    """Every figure keeps a photo even when nothing is for sale: the first listing photo seen
    for it is remembered in updater/listing-photos.json (official NECA pictures still win)."""
    try:
        cache = json.loads(PHOTOS_FILE.read_text(encoding="utf-8"))
        if not isinstance(cache, dict):
            cache = {}
    except (OSError, ValueError):
        cache = {}
    changed = False
    for fid, listings in by_fig.items():
        fig = catalog["by_id"].get(fid)
        if not fig or fig.get("other") or fid in cache:
            continue
        for l in listings:
            if safe_url(l.get("image")):
                cache[fid] = l["image"]
                changed = True
                break
    if changed:
        PHOTOS_FILE.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return cache


# ===== exact shipping for listings with calculated shipping =====

def load_shipping_cache():
    try:
        data = json.loads(SHIPPING_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def fill_shipping(ebay, by_fig, settings):
    """Search results have no price for calculated shipping, so look those listings up
    (20 per call) and remember the answer. Returns how many lookups were made."""
    cache = load_shipping_cache()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    limit = int(settings.get("max_shipping_lookups_per_update", 10))
    listings = [l for ls in by_fig.values() for l in ls if l.get("source") == "ebay"]
    current_ids = {l["id"] for l in listings}
    for l in listings:
        hit = cache.get(l["id"])
        if l["shipping"] is None and hit and hit.get("shipping") is not None:
            l["shipping"] = hit["shipping"]
    todo = [l for l in listings if l["shipping"] is None and (cache.get(l["id"]) or {}).get("checked") != today]
    todo.sort(key=lambda l: l["price"])
    looked = 0

    batch_ok = True
    for start in range(0, min(len(todo), BATCH_SIZE * MAX_BATCH_CALLS), BATCH_SIZE):
        chunk = todo[start:start + BATCH_SIZE]
        try:
            details = ebay.get_items([l["id"] for l in chunk])
        except NotAllowed as e:
            print(f"eBay does not allow batch lookups for these keys, using single lookups ({e})")
            batch_ok = False
            break
        except TemporaryError as e:
            print(f"Batch shipping lookup paused this hour ({e})")
            break
        by_id = {d.get("itemId"): d for d in details}
        for l in chunk:
            looked += 1
            cost = shipping_cost(by_id[l["id"]]) if l["id"] in by_id else None
            cache[l["id"]] = {"shipping": cost, "checked": today}
            if cost is not None:
                l["shipping"] = cost
    if batch_ok:
        todo = []

    for l in todo[:max(0, limit)]:
        try:
            detail = ebay.get_item(l["id"])
        except TemporaryError as e:
            print(f"Shipping lookup paused this hour ({e})")
            break
        looked += 1
        cost = shipping_cost(detail)
        cache[l["id"]] = {"shipping": cost, "checked": today}
        if cost is not None:
            l["shipping"] = cost
    cache = {k: v for k, v in cache.items() if k in current_ids}  # forget sold or ended listings
    try:
        SHIPPING_FILE.write_text(json.dumps(cache, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as e:
        print(f"Could not save shipping-cache.json ({e})")
    sort_listings(by_fig)
    missing = sum(1 for l in listings if l["shipping"] is None)
    print(f"Shipping: looked up {looked} listing(s) this update, {missing} still waiting for a price.")
    return looked


# ===== main =====

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


SHIP_TO_ZIP = os.environ.get("SHIP_TO_ZIP", "").strip()


def write_output(status, by_fig, settings, message="", images=None, store_ok=None, photos=None):
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated": now_iso(),
        "status": status,
        "message": message,
        "store_ok": store_ok,
        "rules": {
            "min_seller_positive_percent": settings["min_seller_positive_percent"],
            "min_seller_ratings": settings["min_seller_ratings"],
            "us_sellers_only": settings["us_sellers_only"],
            "shipping_for_zip": bool(SHIP_TO_ZIP.isdigit() and len(SHIP_TO_ZIP) == 5),
            "neca_store": bool(settings.get("show_neca_store", True)),
        },
        "images": images or {},
        "photos": photos or {},
        "figures": {fid: {"listings": ls} for fid, ls in (by_fig or {}).items() if ls},
    }
    tmp = OUT_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(OUT_FILE)


def write_heartbeat():
    """Writes today's date once a day. GitHub turns off hourly jobs on repos with no
    changes for 60 days, so the workflow saves this tiny file daily to stay active."""
    HEARTBEAT_FILE.write_text(datetime.now(timezone.utc).strftime("%Y-%m-%d") + "\n", encoding="utf-8")


def run(client_id, client_secret, session=None, sleep=time.sleep, store_session=None):
    settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    catalog = load_catalog()
    write_heartbeat()

    by_fig = empty_by_figure(catalog)
    pictures, store_ok = add_neca_store(by_fig, catalog, settings, store_session)
    images = update_images(pictures)

    if not client_id or not client_secret:
        print("No eBay keys found yet. Add EBAY_CLIENT_ID and EBAY_CLIENT_SECRET as GitHub secrets.")
        write_output("needs_keys", by_fig, settings, "eBay keys have not been added yet.", images, store_ok, update_photos(by_fig, catalog))
        return 0

    ebay = Ebay(client_id, client_secret, session=session, sleep=sleep, zip_code=SHIP_TO_ZIP)
    try:
        ebay.refresh_token()
    except AuthError as e:
        print(f"PROBLEM: {e}")
        write_output("bad_keys", by_fig, settings, "eBay did not accept the keys.", images, store_ok, update_photos(by_fig, catalog))
        return 0
    except TemporaryError as e:
        print(f"eBay is having trouble right now, keeping the last good results online. Details: {e}")
        return 1

    try:
        ebay_by_fig, worked = fetch_all(ebay, catalog, settings)
    except AuthError as e:
        print(f"PROBLEM: {e}")
        write_output("bad_keys", by_fig, settings, "eBay did not accept the keys.", images, store_ok, update_photos(by_fig, catalog))
        return 0

    if worked == 0:
        print("Every eBay search failed, so the last good results stay online.")
        return 1

    if ebay.zip_code:
        try:
            fill_shipping(ebay, ebay_by_fig, settings)
        except AuthError:
            pass  # the listings are still good without exact shipping

    for fid, ls in ebay_by_fig.items():
        by_fig[fid].extend(ls)
    sort_listings(by_fig)

    total = sum(len(l) for l in by_fig.values())
    for f in catalog["figures"]:
        if by_fig[f["id"]]:
            print(f"{f['name']}: {len(by_fig[f['id']])} listing(s)")
    write_output("ok", by_fig, settings, images=images, store_ok=store_ok, photos=update_photos(by_fig, catalog))
    print(f"Done. {total} listing(s) across {sum(1 for l in by_fig.values() if l)} figures. eBay calls used this update: {ebay.calls}.")
    return 0


if __name__ == "__main__":
    sys.exit(run(os.environ.get("EBAY_CLIENT_ID", "").strip(), os.environ.get("EBAY_CLIENT_SECRET", "").strip()))
