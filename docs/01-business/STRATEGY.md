# Business Strategy — NORDVIK

> Consulted hat: **Senior Business Strategist**. Owner: Founder.
> **Framing:** this is a *simulated* business used as a portfolio artifact. The analysis is done as if the store were real — with explicit assumptions and confidence levels — but this is **decision-support, not financial or legal advice**, and no outcome is guaranteed.

---

## Context

- **Business:** direct-to-consumer e-commerce store selling household goods and home furniture ("IKEA-inspired" category and brand feel).
- **Primary market:** Indonesia (Greater Jakarta first; tier-1 cities later). **Interface language:** English (chosen so international reviewers/clients can read the store and the strategy).
- **Strategic question:** *Which business model should a solo founder with strong engineering but limited retail/supply-chain capability choose, so that the store is both credible as a business and finishable as a portfolio project?*
- **Constraints:** one person; no capital for inventory or paid acquisition; no brand, supply chain, or logistics capability; must ship a polished demo.

---

## Strategic Analysis

> Evidence below is drawn from public market-research summaries (Mordor Intelligence, ECDB, Verified Market Research, Ken Research). Figures are third-party **estimates** and are directional. Confidence: **Low–Medium**.

- [ ] **STRAT-ANALYSIS-1.1 [Market size & growth]**
  - **Finding:** Indonesia's furniture e-commerce alone is ~**US$4.4B (2025)**, growing **5–10% YoY**; the broader home-furniture market is ~**US$4.9B (2025)** heading to ~**US$6.3B by 2031** (~4.2% CAGR). Overall Indonesian e-commerce was ~**US$58B (2024)** with high-teens CAGR.
  - **Evidence:** ECDB (furniture e-commerce US$4,410m, 2025); Mordor Intelligence (home furniture US$4.94B→US$6.32B); Verified Market Research (e-commerce US$58.4B, 2024).
  - **Implication:** The category is large and growing, but not explosive — growth comes mostly from *channel shift online*, not category expansion.
  - **Confidence:** Medium (multiple independent sources roughly agree on order of magnitude).

- [ ] **STRAT-ANALYSIS-1.2 [Channel shift is the tailwind — and the risk]**
  - **Finding:** Online is still only ~**10–15%** of furniture retail, projected to reach ~**15–20% in 2026**. But marketplaces (**Tokopedia, Shopee, Lazada**) dominate online furniture sales.
  - **Evidence:** industry commentary on online penetration; ECDB lists Tokopedia/Shopee/Lazada as the largest online furniture retailers.
  - **Implication:** The structural opportunity is the move online; the structural threat is that marketplaces, not brand stores, capture that move. A standalone store must win on **brand, curation, and experience** — it cannot win on selection or price against marketplaces.
  - **Confidence:** Medium.

- [ ] **STRAT-ANALYSIS-1.3 [Conversion economics are brutal — experience is the battleground]**
  - **Finding:** In Indonesian furniture e-commerce, add-to-cart is ~**10–10.5%** and **cart abandonment is ~92%**.
  - **Evidence:** ECDB conversion-funnel benchmarks, 2025.
  - **Implication:** ~9 in 10 carts are abandoned. The winning levers are **trust, shipping-cost transparency, and checkout UX** — exactly the levers a well-engineered store controls. This directly justifies the engineering investment.
  - **Confidence:** Medium.

- [ ] **STRAT-ANALYSIS-1.4 [Category & price structure]**
  - **Finding:** Living/dining-room furniture leads at ~**31%** of the home-furniture market; **wood** is ~**61.7%** by material; the **mid-range** price band is ~**48.6%** of the market. Specialty stores still hold ~**40.9%** of distribution, but online is the fastest-growing channel (~6.7% CAGR).
  - **Evidence:** Mordor Intelligence, 2025.
  - **Implication:** Position in the **mid-range**, lead with living/dining furniture, and lean into a "designed but affordable" story. Mid-range is the largest, most contested, and most brand-sensitive band.
  - **Confidence:** Medium.

- [ ] **STRAT-ANALYSIS-1.5 [Competitive landscape]**
  - **Finding:** Incumbents split into (a) *omnichannel brands* — **IKEA Indonesia**, Informa (Home Center), **Ruparupa** (Kawan Lama), Ace Hardware, JYSK; (b) *online-first* — **Dekoruma** (and **Fabelio**, which collapsed — a cautionary tale about unit economics); and (c) *marketplaces* — Tokopedia, Shopee, Lazada.
  - **Evidence:** Ken Research competitor list; ResearchAndMarkets; market commentary.
  - **Implication:** IKEA/Informa own brand + showroom; marketplaces own traffic. The defensible white space for a new entrant is a **focused, design-led, small-space catalog** with a *better digital experience* than the incumbents' — not a broad catalog.
  - **Confidence:** Medium.

- [ ] **STRAT-ANALYSIS-1.6 [Internal capability gap]**
  - **Finding:** The founder has **strong software engineering** and **data engineering** capability but **no supply chain, brand, logistics, or paid-marketing capability**.
  - **Evidence:** Founder background (IT since 2017; backend + data engineering).
  - **Implication:** Any model requiring inventory, warehousing, or supplier management is a poor fit. The model must **play to the founder's strengths** (product and engineering) and stay asset-light.
  - **Confidence:** High.

### Porter's Five Forces (quick pass)

| Force | Intensity | Note |
|---|---|---|
| Rivalry | High | Fragmented; marketplaces + incumbents + thousands of small sellers. |
| Supplier power | Medium | Many furniture suppliers; differentiation comes from curation, not supply. |
| Buyer power | High | Low switching cost; price transparency everywhere. |
| Substitutes | Medium | Second-hand, DIY, marketplace alternatives. |
| New entrants | High | Low barriers online; the moat is brand/experience, not capital. |

**Net:** structurally unattractive on price — which is exactly why the strategy must compete on **brand and experience, not cost**.

### Customer segmentation

- [ ] **SEG-A [Urban first-home / renters, 24–35, Greater Jakarta]**
  - Needs: furnish a small apartment affordably; small-footprint, multi-function pieces; fast delivery.
  - Willingness to pay: mid-range; highly price- and trust-sensitive.
- [ ] **SEG-B [Young families upgrading, 30–40]**
  - Needs: living/dining furniture, durability, kid-safe materials.
  - Willingness to pay: mid-range to upper-mid.
- [ ] **SEG-C (secondary) [Remote workers fitting a home office]**
  - Needs: desks, chairs, storage on a modest budget.

**Primary target:** **SEG-A** — large, underserved on *small-space* curation, and the natural fit for a design-led brand.

---

## Brand name proposal

- [ ] **STRAT-NAME-1.1 [Brand name]**
  - **Shortlist:** **NORDVIK** · Nestora · Hemora · Kasa Living.
  - **Recommendation:** **NORDVIK** (Nordic feel, evokes the IKEA reference without copying it; pronounceable in English and Indonesian).
  - **Status:** *Approved* (2026-10-04) — see [`../decisions/ADR-0007-brand-name.md`](../decisions/ADR-0007-brand-name.md).
  - **Confidence:** n/a (a naming judgment).

---

## Strategic Options

- [ ] **STRAT-OPTION-1.1 [A — Curated D2C brand ("IKEA-lite", asset-light)]**
  - **Description:** A single-brand store with a *curated* catalog of mid-range, small-space home goods. Start with dropship/consignment to avoid holding inventory; build a strong brand and a best-in-class digital experience.
  - **Rationale:** Wins on brand + experience (the defensible levers); asset-light; directly showcases engineering; finishable by one person.
  - **Trade-offs:** Thin margins early; dependent on suppliers; must generate its own traffic. **Reversible** — can pivot catalog or add products cheaply.
  - **Fit:** Excellent (plays to engineering + data strengths; avoids supply-chain gap).

- [ ] **STRAT-OPTION-1.2 [B — Multi-vendor marketplace]**
  - **Description:** Onboard many sellers; the store is the platform.
  - **Rationale:** Scales selection without inventory; classic marketplace economics.
  - **Trade-offs:** Requires seller onboarding, payouts, disputes, trust & safety — enormous operational surface. **Not finishable** by one person for a portfolio. Poor fit.
  - **Fit:** Poor.

- [ ] **STRAT-OPTION-1.3 [C — Marketplace-native seller (no own site)]**
  - **Description:** Sell exclusively through Tokopedia/Shopee rather than a standalone storefront.
  - **Rationale:** Meets customers where they already are; lowest traffic cost.
  - **Trade-offs:** No brand ownership; no portfolio artifact (the point is to build the store). **Fit:** Poor for this project's goals.

- [ ] **STRAT-OPTION-1.4 [D — Niche: small-space furniture]**
  - **Description:** Own the "small apartment, smart storage" niche with a tightly curated range.
  - **Rationale:** Defensible via focus; clear positioning; matches SEG-A.
  - **Trade-offs:** Smaller TAM; needs strong content/community. **Fit:** Strong — and it *combines* with Option A.

---

## Recommendation

**Recommended path: Option A + Option D — a curated, asset-light, D2C home-goods brand focused on small-space living ("IKEA-lite, small-space-first").**

- **Why:** It is the only option that simultaneously (a) is defensible against marketplaces via brand + experience, (b) is finishable by a solo founder, (c) avoids the supply-chain capability gap via dropship/consignment, and (d) is an excellent showcase of software + data engineering.
- **Trade-offs accepted:** slower revenue ramp, thin early margins, and a real dependency on the founder generating traffic and building a brand.
- **Reversibility:** High — the catalog and channel can change cheaply; the codebase is reusable in every scenario.
- **Kill criteria (what would prove this wrong):** if the store cannot sustain > ~35% gross margin after shipping, or if landing-page→add-to-cart stays under ~5% after experience investment, the model is not working.

### Unit economics — illustrative only

> Numbers are **illustrative placeholders** with stated assumptions; they exist to show the *shape* of the economics, not to forecast. Confidence: **Low**.

| Metric | Illustrative value | Assumption |
|---|---|---|
| Average order value (AOV) | Rp 750,000 (~US$47) | Mid-range single-item + accessory basket |
| COGS | 55% of AOV | Dropship/wholesale cost |
| Shipping | ~near cost | Charged to customer; thin margin |
| **Gross margin** | **~40–45%** | AOV − COGS; before shipping ops |
| CAC (paid) | Rp 150,000–300,000 | Meta/TikTok ads, Indonesia benchmarks |
| Contribution margin | positive only if CAC < ~Rp 250k | This is the central pressure point |
| LTV (12-mo, repeat) | 1.3–1.6× first order | Optimistic; requires retention work |

**Read:** the model only works with **cheap organic traffic** (content, SEO, social) or strong **repeat/AOV** — which is why the engineering quality and the (later) data track matter: they are the levers that reduce CAC and lift conversion.

### Positioning & differentiation

- **For** urban renters and young families in Greater Jakarta **who** need affordable, well-designed, small-space home goods,
- **NORDVIK** is a **design-led home-goods store** that offers a **curated, small-space-first** catalog with a **transparent, fast, trustworthy online buying experience**,
- **unlike** IKEA/Informa (big-box, broad, showroom-centric) and marketplaces (endless, unfiltered, low-trust),
- **because** we compete on curation and experience, not on breadth or price.

**Defensibility:** brand + curation + experience (hard to copy quickly), later reinforced by a data-driven personalization/retention loop.

### Metrics

- **Leading (detect problems early):** landing→PDP rate, PDP→add-to-cart rate, add-to-cart→checkout rate, **cart-abandonment** (benchmark ~92% — the key number to beat), page performance (LCP), organic traffic share.
- **Lagging:** revenue, AOV, gross margin, repeat-purchase rate, contribution margin per order.

- [ ] **GOAL-B1** Beat the ~92% cart-abandonment benchmark (i.e. drive abandonment below ~85%) through experience + transparent shipping.
- [ ] **GOAL-B2** Reach ~45% gross margin at the illustrative AOV.
- [ ] **GOAL-B3** Achieve majority-organic traffic before any paid spend.

### Capability changes required

- Build brand + content capability (the founder's biggest gap) or partner with a designer/content marketer.
- Establish supplier/dropship relationships for the curated catalog.
- Instrument the funnel from day one (feeds the Phase 2 data-engineering track).

---

## Quality checklist

- [x] Analysis grounded in third-party market estimates with sources.
- [x] Four genuinely distinct strategic options evaluated.
- [x] Assumptions and confidence levels stated explicitly.
- [x] Risks and a competitor-response view included.
- [x] Recommendation justified; alternatives presented fairly.
- [x] Priorities translated into measurable metrics.
- [x] Framed as decision-support, not guaranteed outcomes.

## Sources

- ECDB — *Furniture Industry in Indonesia* — https://ecdb.com/resources/sample-data/market/id/furniture
- Mordor Intelligence — *Indonesia Home Furniture Market* — https://www.mordorintelligence.com/industry-reports/indonesia-home-furniture-market
- Verified Market Research — *Indonesia E-commerce Market* — https://www.verifiedmarketresearch.com/product/indonesia-ecommerce-market
- Ken Research — *Indonesia Furniture and Home Retail Market* — https://www.kenresearch.com/indonesia-furniture-and-home-retail-market
