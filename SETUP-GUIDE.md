# NECA Finder: setup guide

NECA Finder is a free website that checks eBay and the official NECA store every hour for new, sealed NECA figures from six lines: Alien, Predator, RoboCop, Terminator, The Thing (1982) and Escape From New York. Each line has its own tab and its own look. Click a figure to see every listing for it.

It works the same way as the Sealed Elves Finder: GitHub runs the check every hour and hosts the site for free. Nothing has to stay running on anyone's PC.

## What it shows

- **eBay listings** that eBay marks as New, from US sellers with at least 95% positive feedback and 50 ratings, whose titles say NECA or Reel Toys (NECA's own label).
- **NECA store listings** for figures that are in stock or on pre-order at store.necaonline.com. These show first on a figure's page.
- Titles that mention opened, loose, used, custom, 3D printed, fake, lots or bundles are hidden. So are things that aren't figures (Head Knockers, plush, Cinemachines, masks, eggs and so on).
- A yellow **Box damage mentioned** tag marks sealed figures whose box is described as damaged. "Battle damaged" is a figure version, so it doesn't count.

## One-time setup

### Step 1: eBay keys (reuse the Elves ones)

eBay gives one Production keyset per account, so use the same two keys as the Elves finder:

1. Sign in at developer.ebay.com, click your name (top right), then **Application Keysets**.
2. Copy the **App ID (Client ID)** and the **Cert ID (Client Secret)** from the Production keyset.

Both sites together stay well under eBay's 5,000 free searches a day (NECA Finder uses about 15 to 25 per update, around 500 a day).

### Step 2: Add the keys to the repository

1. In the `neca-finder` repository, click **Settings**, then **Secrets and variables**, then **Actions**.
2. Click **New repository secret**. Name: `EBAY_CLIENT_ID`. Secret: the App ID. Click **Add secret**.
3. Click **New repository secret** again. Name: `EBAY_CLIENT_SECRET`. Secret: the Cert ID. Click **Add secret**.

The names must be typed exactly as shown.

Optional: to show exact shipping prices for your friend's address, open the **Variables** tab on the same page, click **New repository variable**, name it `SHIP_TO_ZIP` and type his 5-digit ZIP code.

### Step 3: Turn on the website

1. Still in **Settings**, click **Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.

### Step 4: Run the first update

1. Click the **Actions** tab, then **Update NECA listings** on the left.
2. Click **Run workflow**, then the green **Run workflow** button.
3. After 3 to 5 minutes it turns into a green check.
4. Go to **Settings**, then **Pages**. The link at the top, like `https://yourname.github.io/neca-finder/`, is the site. Send that link to your friend.

Also run **Hourly timer** once the same way (tick the box to start right away). It keeps the hourly schedule on time, because GitHub's own schedule often runs late.

## Changing the settings

All the filters live in `updater/settings.json`. Open it on GitHub, click the pencil icon, edit, and click **Commit changes**. The site updates within a few minutes.

- `min_seller_positive_percent` and `min_seller_ratings`: the trusted seller rules (now 95 and 50)
- `show_buy_it_now`, `show_auctions`, `us_sellers_only`: true or false
- `show_neca_store`: set to false to hide NECA store listings
- `hide_words`: titles with any of these are hidden
- `hide_pairs`: titles with both words of a pair are hidden (catches sellers bundling two figures)
- `box_warning_words`: titles with these get the yellow box damage tag

## Adding or changing figures

The figure list lives in `tools/build_catalog.py`. Each line is one figure with the words its eBay titles use. After editing it, run `python3 tools/build_catalog.py` on a PC to rebuild `site/data/catalog.json`, then upload both files. Anything that passes every check but matches no named figure still shows up in the **Other** tile at the bottom of its tab, so nothing gets lost while you wait.

## Fixing problems

- **Banner says "the eBay keys are missing":** redo Step 2. Only NECA store listings show until the keys are in.
- **Banner says "eBay did not accept the keys":** copy the Production keys again. Make sure the keyset isn't marked disabled on the eBay developer site.
- **Banner says listings are more than 4 hours old:** open **Actions**. If a yellow banner says workflows are disabled, click **Enable**, then run **Update NECA listings** once.
- **A figure is filed in the wrong place:** it happens with oddly worded titles. Edit that figure's words in `tools/build_catalog.py`, or add a word to its "not" list.

## Good to know

- **"Sealed" is a best effort.** eBay has no sealed checkbox. The site keeps only listings marked New and hides titles that suggest otherwise, but a dishonest seller can still mislabel a listing, so always check the photos.
- **95% feedback is lenient.** Most solid sellers sit at 99% or higher. Raise it to 98 if bad sellers slip through.
- **Pictures:** figures use NECA's official photo when the NECA store has (or had) that figure, and the cheapest eBay listing's photo otherwise.
- **Costs:** eBay's API, GitHub and the website are all free for this.
