#!/usr/bin/env python3
"""Morning Digest — Daily Finance & Tech News Fetcher"""

import feedparser
import datetime
import html
import re
import os
import urllib.request
import concurrent.futures

# ── India Standard Time (UTC+5:30) ────────────────────
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
now = datetime.datetime.now(IST)
today_str = now.strftime("%A, %d %B %Y")
day_of_year = now.timetuple().tm_yday

# ── Daily Vocabulary — 5 terms shown per day, rotating ───────────────
VOCABULARY = [
    # ── Markets & Instruments ──────────────────────────────────────────
    ("UCITS", "Undertakings for Collective Investment in Transferable Securities — the EU's gold-standard fund wrapper that grants a single authorisation passport across all member states. Strict rules on eligible assets, concentration limits (5/10/40 rule), daily liquidity, and mandatory KIIDs make UCITS the default vehicle for cross-border retail fund distribution. Most ETFs listed on Euronext, Xetra, and LSE are UCITS-compliant, making it the dominant framework for European and increasingly global fund launches."),
    ("Yield Curve Control (YCC)", "A central bank policy that pins the yield on a specific government bond maturity at a target level by standing ready to buy unlimited quantities. The Bank of Japan used YCC to cap 10-year JGB yields, distorting global fixed-income pricing and forcing other central banks to react. When credibility falters, the cost of defending the peg can become fiscally prohibitive, as speculative pressure mounts against a capped rate."),
    ("Delta Hedging", "A technique that keeps an options book market-neutral by continuously adjusting the position in the underlying asset so that small price moves produce zero net P&L. Delta itself (the option's sensitivity to the underlying) changes as price moves — requiring constant rebalancing called gamma trading. Market makers delta-hedge to isolate and sell volatility risk (Vega) rather than directional exposure, making it the backbone of systematic options dealing."),
    ("Contango vs Backwardation", "Contango describes a futures curve where longer-dated contracts trade above spot — typical when storage costs and financing are positive, as in oil. Backwardation is the reverse: spot exceeds futures, signalling near-term supply tightness or high convenience yield. The difference between rolling futures contracts in contango erodes returns for commodity ETF holders — a structural drag that can amount to several percentage points annually and is often missed by retail investors."),
    ("Smart Order Routing (SOR)", "Algorithms that scan multiple trading venues in real time — exchanges, dark pools, MTFs — and split or route orders to achieve best execution. SOR weighs price, size, speed, and fill probability simultaneously. Under MiFID II and similar regimes, brokers must demonstrate best execution to clients, making SOR infrastructure central to compliance as well as competitiveness. Latency (measured in microseconds) is the key battleground for institutional SOR systems."),
    ("Factor Investing / Smart Beta", "A systematic approach that tilts portfolios toward documented risk premia — Value, Momentum, Quality, Low Volatility, Size — rather than market-cap weighting. Originally an academic insight (Fama-French), it has been industrialised into a multi-trillion-dollar ETF category. Factor premia are cyclical and prone to crowding: when too much capital chases the same signal the factor's premium compresses and drawdowns steepen, requiring investors to have a long horizon and the conviction to hold through underperformance."),
    ("Implied Volatility Surface", "A three-dimensional map of implied volatilities across strike prices and expiry dates derived by inverting the Black-Scholes formula from live option prices. The surface reveals skew (put options typically trade richer than calls, reflecting crash hedging demand) and term structure (long-dated IV often exceeds short-dated IV). Traders arbitrage inconsistencies across the surface; central banks and macro managers read it as a real-time gauge of tail-risk pricing."),
    ("Perpetual Futures (Perps)", "A derivative product pioneered by crypto exchanges that mimics a futures contract but never expires. Instead, a periodic funding rate — paid hourly or every 8 hours — keeps the perp price anchored to spot by transferring money from longs to shorts (or vice versa) based on the premium. High leverage (up to 125× on some platforms) and 24/7 trading make perps the dominant instrument for crypto speculation, generating billions in daily open interest across Bitcoin and Ethereum."),
    ("MEV – Maximal Extractable Value", "Profit that miners (in Proof-of-Work) or validators (in Proof-of-Stake) can extract beyond standard block rewards by selectively including, reordering, or censoring transactions within a block. MEV strategies include front-running (inserting a buy before a large trade), sandwich attacks (bracketing a victim transaction), and liquidation racing. Ethereum's MEV ecosystem, mediated by Flashbots, redistributes hundreds of millions of dollars annually and has prompted architectural debates about fairness and protocol design."),
    ("T+1 Settlement", "The compressed settlement cycle under which securities transactions are finalised one business day after trade date, down from the previous T+2 standard. The US and Canada moved to T+1 in May 2024; India and China already settle some markets at T+1 or T+0. Faster settlement reduces counterparty risk and collateral requirements but compresses the window for failed-trade correction, currency conversion for cross-border flows, and securities lending recall — creating operational pressure on custodians, prime brokers, and asset managers."),
    ("Prime Brokerage", "A bundled suite of services offered by large banks and broker-dealers to hedge funds: securities lending (for short-selling), leveraged financing, trade execution, custody, and risk reporting. The prime broker stands between the hedge fund and the market, netting exposures and providing consolidated reporting. PB relationships are strategically important — funds often use multiple primes post-Lehman to reduce concentration risk. Prime brokerage is one of the most profitable businesses in institutional banking, with financing spreads and stock-loan fees as key revenue drivers."),
    ("Securities Lending", "The temporary transfer of securities from a lender (often a pension fund or ETF) to a borrower (typically a hedge fund) in exchange for collateral (cash or other securities) and a fee. Borrowers use lent stock to cover short positions. Lenders earn incremental yield on an otherwise idle portfolio — securities-lending revenue can offset a meaningful portion of ETF management fees. Risks include counterparty default and the reinvestment risk of cash collateral, both highlighted during the 2008 crisis."),
    ("CCP – Central Counterparty Clearing", "An entity that interposes itself between buyer and seller in a derivatives or securities trade, becoming the buyer to every seller and the seller to every buyer. By multilaterally netting exposures and collecting margin from all participants, CCPs dramatically reduce systemic risk — a lesson drawn from bilateral OTC market failures in 2008. Post-crisis regulation (EMIR, Dodd-Frank) mandated clearing of standardised derivatives through CCPs, shifting trillions of notional from bilateral to cleared form and concentrating risk in systemically critical nodes."),
    ("Value at Risk (VaR)", "A statistical estimate of the maximum portfolio loss over a specified horizon at a given confidence level — e.g., '1-day 99% VaR of $10 million' means losses exceeding $10M should occur less than 1% of trading days. Regulators use VaR to set market-risk capital requirements. Critics note VaR says nothing about losses beyond the confidence threshold (tail risk) and can encourage false precision. Expected Shortfall (ES / CVaR) — the average loss in the worst scenarios — has largely replaced VaR in the Basel framework for this reason."),
    ("Repo / Reverse Repo", "A repurchase agreement is the sale of a security combined with a simultaneous agreement to buy it back at a specified price on a future date — effectively a collateralised short-term loan. From the lender's perspective it is a reverse repo. The US Fed's overnight reverse repo (ON RRP) facility is a critical monetary policy tool, soaking up excess bank reserves by letting money market funds park cash with the Fed. Repo markets underpin the entire short-term dollar funding system and can freeze catastrophically during stress, as in September 2019."),
    ("CBDC – Central Bank Digital Currency", "A sovereign digital currency issued directly by a central bank, existing as a liability of the state rather than a commercial bank. Retail CBDCs give households direct central-bank accounts; wholesale CBDCs target interbank settlement. Over 130 countries are exploring CBDCs. China's e-CNY is the most advanced large-economy deployment. Key design questions include privacy versus traceability, disintermediation risk to commercial banks, and programmable money features. The BIS Innovation Hub coordinates research and cross-border CBDC interoperability pilots."),
    ("MiCA – Markets in Crypto-Assets Regulation", "The EU's comprehensive regulatory framework for crypto-assets, fully applicable from December 2024. MiCA creates a licensing passport for crypto-asset service providers (CASPs) across the EU, imposes reserve, redemption, and disclosure requirements on stablecoin issuers, and bans anonymous crypto transactions above €1,000. It is the world's most detailed crypto regulatory framework and a template other jurisdictions are studying. Non-compliant exchanges serving EU customers face blocking or enforcement action under the regime."),
    ("Embedded Finance", "The integration of financial services — payments, lending, insurance, investment — directly into non-financial platforms and apps at the point of need. A ride-hailing app offering instant earnings access, an e-commerce platform providing BNPL at checkout, or a SaaS tool offering working-capital loans to its merchant customers are all embedded finance examples. Enabled by Banking-as-a-Service (BaaS) APIs, embedded finance is projected to become a multi-trillion-dollar market as distribution shifts from banks to the platforms where consumers and businesses already spend time."),
    ("DORA – Digital Operational Resilience Act", "An EU regulation (effective January 2025) that harmonises ICT risk management, incident reporting, and third-party oversight for the financial sector. All regulated financial entities — banks, insurers, investment firms, CCPs, crypto-asset service providers — must test their digital resilience, including TLPT (Threat-Led Penetration Testing), and manage concentration risk in critical cloud and technology vendors. DORA effectively gives regulators direct oversight of cloud providers like AWS, Azure, and GCP when they serve EU financial firms."),
    ("ISO 20022", "A global standard for electronic data interchange between financial institutions, replacing dozens of legacy messaging formats (MT, NACHA, etc.) with structured XML/JSON data rich enough to carry full remittance information. SWIFT is migrating the cross-border payments network to ISO 20022 through 2025. The richer data enables straight-through processing, better AML screening, and real-time payment reconciliation — but migration requires significant investment from correspondent banks, corporates, and payment infrastructure globally."),
    ("Payment for Order Flow (PFOF)", "A practice where retail brokers route customer orders to market makers in exchange for a per-share rebate. Critics argue it creates a conflict of interest — the broker is incentivised to send orders to the highest-paying venue rather than the one offering best execution. The EU banned PFOF under MiFID II; the SEC has repeatedly reviewed but not banned it in the US, where it underpins the zero-commission model at Robinhood and others. The debate centres on whether retail investors receive better prices through internalisation or on-exchange competition."),
    ("Liquidity Coverage Ratio (LCR)", "A Basel III requirement that banks hold sufficient high-quality liquid assets (HQLA — cash, central bank reserves, government bonds) to cover 30 days of net cash outflows in a stress scenario. The minimum LCR is 100%. The March 2023 US regional banking crisis exposed the LCR's limitations: Silicon Valley Bank was exempt as a mid-size bank, and uninsured depositor runs proved faster than the 30-day horizon assumed. LCR compliance is now a key metric for institutional counterparty assessment."),
    ("Gamma Squeeze", "A market dynamic where a rapid rise in an asset's price forces options dealers who sold call options to buy increasing quantities of the underlying to stay delta-neutral — which itself pushes the price higher, forcing more buying. The feedback loop can accelerate dramatically when open interest is concentrated at nearby strikes. The January 2021 GameStop episode was a textbook gamma squeeze amplified by retail co-ordination, pushing the stock from ~$20 to $483 in days and causing billions in losses at short-selling hedge funds."),
    ("Information Ratio (IR)", "A measure of active portfolio management quality: (Portfolio Return − Benchmark Return) ÷ Tracking Error. It quantifies how much active return (alpha) is generated per unit of active risk taken. An IR above 0.5 is considered respectable; above 1.0 is exceptional and rarely sustained. Unlike the Sharpe Ratio, which uses total volatility, the IR isolates the skill of active bets relative to the chosen benchmark — making it the primary metric for evaluating active fund managers over a full market cycle."),
    ("Collateral Transformation", "A service where an institution swaps lower-quality assets (equities, high-yield bonds) for high-quality liquid assets (government bonds, cash) that can be posted as margin or collateral at CCPs or for repo transactions. Post-2008 mandatory clearing requirements dramatically increased the demand for HQLA collateral, creating a structural shortage. Collateral transformation desks at large custodians and prime brokers bridge this gap for a fee, but also introduce additional counterparty and liquidity risk into the system."),
    ("Algorithmic Market Making", "Automated quoting of two-sided markets (bid and ask) across many securities simultaneously, using statistical models to calibrate spread, size, and inventory targets. Algorithmic market makers earn the bid-ask spread while managing the risk of holding inventory during adverse price moves. Sophisticated models incorporate order-book dynamics, short-term momentum, and correlated assets. In equities and FX, algorithmic market making has essentially replaced human specialists, compressing spreads dramatically while creating new fragility under extreme conditions."),
    ("Open Interest", "The total number of outstanding derivative contracts (futures or options) that have not been settled. Rising open interest alongside rising price suggests new money entering long positions — a bullish confirmation. Rising open interest with falling price suggests new short positions — bearish conviction. Declining open interest at any price level suggests existing positions are being closed. OI analysis is standard practice for commodity traders, crypto perp traders, and equity options strategists reading the intensity of market conviction."),
    ("Alpha Decay", "The deterioration of a systematic trading signal's predictive power over time as more capital exploits it. Once an academic paper documents a factor anomaly, assets flow in until arbitrage pressure eliminates the excess return. Quant funds track half-life of signals — the time for return to erode by half — when sizing positions and retiring strategies. Frequent rebalancing, transaction costs, and market impact all accelerate decay. Managing alpha decay is arguably the central operational challenge in quantitative asset management."),
    ("Carry Trade", "Borrowing in a low-interest-rate currency (e.g., Japanese yen) and investing in a higher-yielding currency or asset. Profit equals the interest rate differential minus financing and hedging costs. The key risk: adverse currency moves can swiftly erase accumulated carry, particularly during risk-off episodes when high-yield currencies depreciate sharply against funding currencies. The unwinding of massive yen carry trades triggered a global equity flash crash in August 2024, illustrating how leverage embedded in the FX carry trade can transmit shocks across asset classes."),
    ("Repo Rate", "The rate at which a central bank lends short-term funds to commercial banks against collateral. Raising the repo rate makes credit costlier across the economy, cooling inflation; cutting it stimulates borrowing and growth. In India the RBI repo rate is the primary monetary policy lever — a cut of 25 bps in April 2025 brought it to 6%. The US equivalent is the Federal Funds Rate target range, while the ECB uses its main refinancing operations rate. Repo rate changes propagate instantly to overnight money markets and, with a lag, to retail lending rates."),
    ("Stress Testing / DFAST", "Regulatory exercises that simulate severe but plausible scenarios — deep recession, sharp rate spikes, asset price crashes — to assess whether banks hold sufficient capital to absorb losses and keep lending. In the US, the Dodd-Frank Act Stress Test (DFAST) and Fed CCAR apply to banks above $100B in assets. The EBA runs EU-wide stress tests biennially. Scenarios are published in advance; failure to pass constrains dividend payments and buybacks. Post-SVB, regulators are revisiting scenario design to capture faster-moving deposit-run dynamics."),
    ("SWIFT gpi – Global Payments Innovation", "An overlay service on the SWIFT network that gives cross-border payment participants end-to-end tracking, same-day settlement in most corridors, and full transparency of fees and FX deductions. Adopted by over 4,000 banks, gpi now carries the majority of SWIFT cross-border payments. It is a competitive response to fintech challengers (Wise, Ripple) and a stepping stone toward the ISO 20022 migration. The ultimate ambition — instant, frictionless cross-border payment — remains a goal for the next phase."),
    ("BaaS – Banking as a Service", "A model where licensed banks expose their regulated infrastructure — accounts, payments, card issuance, lending — via APIs to non-bank businesses who build financial products on top. BaaS providers include Railsbank, Synapse (now in receivership), and solarisBank in Europe. Brands from airlines to supermarkets launch co-branded cards and wallets without needing a banking licence. Regulatory scrutiny has intensified after several BaaS partnerships collapsed, leaving end customers unable to access funds — prompting the OCC, Fed, and FDIC to tighten oversight of bank-fintech relationships."),
    ("RegTech", "Technology solutions that help financial institutions meet regulatory requirements more efficiently — automating transaction monitoring, KYC onboarding, regulatory reporting, and model validation. The global RegTech market exceeded $12B in 2024. AI-powered tools can screen millions of transactions for suspicious patterns far faster than rule-based systems. Regulators themselves are deploying SupTech (supervisory technology) to analyse firm-level data in real time rather than relying on periodic reporting. The line between RegTech vendor and regulated entity is blurring as the former access sensitive data."),
    ("Drawdown", "The peak-to-trough decline in portfolio value over a given period. Maximum Drawdown captures the worst historical loss from any peak — a critical risk metric for evaluating strategies and setting investor expectations. A 30% drawdown requires a 43% recovery gain just to return to flat, illustrating the asymmetric mathematics of losses. Time to recovery (drawdown duration) matters as much as magnitude: a strategy that fully recovers in three months is far less damaging operationally than one that takes three years."),
    ("Tokenisation of Real-World Assets (RWA)", "Converting legal ownership rights in physical or financial assets — real estate, treasury bills, private credit, commodities — into digital tokens on a blockchain. RWA tokenisation eliminates manual settlement processes, enables fractional ownership, and creates 24/7 secondary liquidity. BlackRock's BUIDL fund and Franklin Templeton's on-chain money market fund are early institutional benchmarks. The BIS estimates the market could reach $16 trillion by 2030 if regulatory frameworks and interoperability standards mature — but custodial rights, insolvency treatment, and cross-chain settlement remain unresolved."),
    ("Dark Pool", "A private trading venue where large institutional orders execute away from public exchanges, keeping order details hidden until after execution. This protects block orders from market impact — a fund selling 5 million shares on-exchange would visibly move the price against itself. Dark pools account for roughly 15% of US equity volume. Post-MiFID II, European dark pool usage is restricted by double volume caps (DVC). Critics argue dark pool opacity fragments price discovery and disadvantages retail investors who can only access lit market prices."),
    ("Sharpe Ratio", "A risk-adjusted return metric calculated as (Portfolio Return − Risk-Free Rate) ÷ Standard Deviation of Returns. A ratio above 1 is considered solid; above 2 is exceptional and rare at scale. It rewards high returns while penalising volatility, making it the standard tool for comparing strategies with different risk profiles. Critical limitations: it treats upside and downside volatility equally, and it can be gamed by strategies that produce steady gains with occasional catastrophic losses (short volatility, carry). The Sortino Ratio addresses this by penalising only downside deviation."),
    ("Impermanent Loss", "A risk unique to liquidity providers in decentralised exchange AMMs (Uniswap, Curve). When the price ratio of the two pooled tokens shifts, the AMM's constant-product formula automatically rebalances — leaving the LP with less of the outperforming asset and more of the underperformer relative to simply holding both. The 'impermanent' label reflects that the loss only crystallises on withdrawal; if prices revert, it disappears. In practice, high-volatility pairs frequently produce impermanent losses that exceed trading fee income, making pool selection a critical skill in DeFi liquidity provision."),
    ("Market Microstructure", "The study of how trading mechanisms, information, and participant behaviour determine prices and transaction costs at the granular level. Key concepts include bid-ask spread, order book depth, price impact, latency, and adverse selection. Microstructure insights drive exchange design (continuous versus periodic auctions), trading algorithm development, and transaction cost analysis (TCA). High-frequency traders exploit microstructure patterns measured in microseconds; institutional desks use microstructure models to minimise market impact when executing large orders."),
    ("Duration", "A bond's sensitivity to interest rate changes, expressed in years. A modified duration of 7 means a 1 percentage-point rise in yields causes an approximate 7% price decline. Duration is additive across a portfolio, letting managers express macro rate views by shortening (defensive) or extending (bullish on rates). Convexity — the second-order curvature of the price-yield relationship — matters for large rate moves: a bond with positive convexity gains more than its duration predicts when rates fall and loses less when rates rise."),
    ("Basis Points (bps)", "A unit equal to 0.01 percentage point, the universal language of rate and spread changes in fixed income, FX, and derivatives. 100 bps equals 1%. Using bps avoids percentage-of-percentage confusion — a spread widening from 2% to 2.5% is '50 bps', not '25%'. Central bank communications, swap pricing, and credit spread analysis all use bps as the default unit. When traders say a bond 'moved 5 bps', they mean the yield changed by 0.05 percentage points, which translates to a specific price move depending on duration."),
    ("Embedded Payments / Super App", "The convergence of payments, lending, investments, and lifestyle services within a single platform — following the WeChat and Alipay model. A super app controls the customer relationship end-to-end, generating float on stored value, monetising data, and cross-selling financial products at marginal cost. Grab (Southeast Asia), Paytm (India), and aspirants across MENA and Africa are pursuing this model. Regulators worry about systemic risk concentration and data monopolies; established banks worry about disintermediation from the customer relationship they once owned."),
    ("Cross-Margining", "A risk management framework that allows margin offsets between correlated positions across different asset classes or exchanges. Instead of posting full initial margin for each position separately, correlated offsetting positions (e.g., long equity futures and short equity options) share a single margin pool. CCPs like OCC and CME offer cross-margining programmes that can reduce capital requirements by 30–60% for sophisticated portfolios. Post-Archegos, prime brokers tightened cross-margining terms after discovering that concentrated positions disguised as diversified portfolios could unwind catastrophically."),
    ("VWAP / TWAP", "Volume-Weighted Average Price and Time-Weighted Average Price are execution benchmarks and algorithmic trading strategies. VWAP weights the average price by volume, reflecting the 'true' average trade price across a session. TWAP simply averages prices evenly over time. Institutional desks measure execution quality against VWAP — beating VWAP means buying below or selling above the session average. TWAP algorithms minimise market impact for illiquid securities by spreading large orders evenly over time, accepting price uncertainty in exchange for reduced signalling risk."),
    ("Funding Rate (Crypto)", "A periodic payment exchanged between long and short holders of perpetual futures contracts to keep the contract price anchored to the spot index. When the perp trades at a premium to spot (bullish sentiment), longs pay shorts; when below spot (bearish), shorts pay longs. Funding rates are a real-time sentiment indicator — annualised rates above 50% signal extreme leverage and precede sharp corrections as overleveraged longs are liquidated. Basis traders simultaneously hold spot long and perp short to harvest funding without directional exposure."),
    ("AUM – Assets Under Management", "The total market value of all capital a manager oversees on behalf of clients, encompassing discretionary and advisory mandates. AUM is the primary scale metric in asset management — it drives management fee revenue (typically 0.03–2% annually depending on strategy) and signals market standing. Global AUM surpassed $120 trillion in 2024. Paradoxically, AUM growth can destroy alpha: a $100M hedge fund can exploit small opportunities invisible to a $10B fund, which moves markets when it trades — illustrating the capacity constraints that erode performance at scale."),
    ("Momentum Factor", "A quantitative anomaly where assets that have recently outperformed continue to outperform over the next 3–12 months, and vice versa. Documented across equities, bonds, commodities, and currencies, momentum is one of the most robust and persistent risk premia in finance. It is believed to arise from slow incorporation of information (under-reaction) followed by trend-chasing behaviour (over-reaction). The key risk is momentum crash — a sudden, violent reversal during market stress when crowded momentum trades unwind simultaneously, amplifying losses."),
    ("Liquidity Pool (DeFi)", "A smart-contract-held reserve of two or more tokens that enables decentralised trading without a traditional order book. Traders swap directly against the pool; the price adjusts automatically via a bonding curve (e.g., x × y = k in Uniswap v2). Liquidity providers deposit both tokens and earn a proportional share of trading fees. Concentrated liquidity (Uniswap v3) lets providers focus capital around a price range, earning higher fees but requiring active management. Total value locked (TVL) in liquidity pools across DeFi exceeded $80B at peak and serves as the sector's headline size metric."),
    ("Open Banking / PSD3", "Open Banking mandates that banks share customer financial data with authorised third parties via APIs, with explicit consent. PSD2 (EU, 2018) ignited the movement; PSD3 (expected 2026) strengthens real-time payment initiation rights, extends open finance to savings and investments, and tightens authentication standards. In India, the Account Aggregator framework operationalised open banking for 1 billion+ account holders from 2021. The next frontier — open finance — extends data sharing to insurance, pensions, and mortgages, enabling holistic financial planning tools and personalised product offers across providers."),
    ("Prime of Prime (PoP)", "A tier of broker-dealers that provides smaller FX and CFD brokers access to institutional liquidity from tier-1 prime brokers (Goldman, JPMorgan, UBS) that would not onboard them directly due to credit and volume thresholds. PoPs aggregate and repackage tier-1 liquidity, adding markup for risk and services. The UAE hosts several major PoP operations through the DIFC and ADGM free zones. Regulatory scrutiny of PoP credit risk grew after several mid-tier brokers collapsed, leaving retail clients unable to access positions."),
    ("Regulatory Capital / CET1", "Common Equity Tier 1 (CET1) is the highest-quality capital a bank holds — retained earnings and common shares — used as the primary loss-absorbing buffer. Under Basel III, globally systemically important banks (G-SIBs) must maintain CET1 ratios of at least 7–13% of risk-weighted assets. CET1 ratios are the headline metric for bank capital strength; a ratio falling below regulatory minimums triggers automatic restrictions on dividends and bonuses. The 2023 US regional bank failures renewed focus on unrealised losses in held-to-maturity portfolios that Basel III's CET1 framework did not fully capture."),
    ("Transaction Cost Analysis (TCA)", "A quantitative framework for measuring the total cost of executing a trade, covering explicit costs (commission, taxes) and implicit costs (market impact, timing risk, opportunity cost). Implementation Shortfall — the difference between the decision price and average execution price — is the most comprehensive TCA metric. Regulators under MiFID II require investment firms to report on execution quality annually. Sophisticated TCA systems decompose costs by broker, venue, algorithm, and market conditions, enabling continuous improvement in trading desk performance."),
    ("Dispersion Trading", "A volatility arbitrage strategy that sells index options (implied correlation is rich) while buying options on the index's constituents (cheaper individually). The trade profits when index correlation is lower than the market's implied level — i.e., stocks move independently rather than in lockstep. Correlation spikes during market stress, making dispersion trades vulnerable to the same left-tail events that damage most risk strategies. It is a staple of volatility desks at large banks and quantitative hedge funds, generating steady carry in calm markets at the cost of crash exposure."),
    ("Collateral Management", "The operational and strategic process of allocating, monitoring, and optimising assets pledged against financial obligations — margin calls, repo transactions, derivatives exposure, and securities lending. Post-2008 clearing mandates tripled the demand for high-quality collateral globally. Collateral management systems track eligibility, haircuts, substitution rights, and cross-border legal enforceability in real-time. Collateral optimisation — routing the cheapest-to-deliver eligible asset to each obligation — is a multi-billion-dollar savings opportunity for large institutions with diverse collateral pools."),
]

VOCAB_PER_DAY = 5

# ── RSS Sources ────────────────────────────────────────
SOURCES = {
    "wealth": {
        "label": "Wealth",
        "icon": "💰",
        "color": "#10B981",
        "color_bg": "#ECFDF5",
        "has_subsections": True,
        "subsections": {
            "wealth_management": {
                "label": "Wealth Management",
                "feeds": [
                    ("ET Wealth", "https://economictimes.indiatimes.com/wealth/rssfeeds/837555174.cms"),
                    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
                    ("LiveMint Markets", "https://www.livemint.com/rss/markets"),
                    ("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss"),
                ],
            },
            "fintech_uae": {
                "label": "Fintech & UAE Market",
                "feeds": [
                    ("FintechNews UAE", "https://fintechnews.ae/feed/"),
                    ("Arabian Business", "https://www.arabianbusiness.com/rss/"),
                    ("Gulf Business", "https://gulfbusiness.com/feed/"),
                    ("Khaleej Times", "https://www.khaleejtimes.com/feed"),
                ],
            },
            "funds_etfs": {
                "label": "Funds & ETFs",
                "feeds": [
                    ("CNBC Investing", "https://www.cnbc.com/id/15839069/device/rss/rss.html"),
                    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/marketpulse/"),
                    ("CNBC Finance", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
                    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
                ],
            },
        },
    },
    "trade": {
        "label": "Trade",
        "icon": "📊",
        "color": "#3B82F6",
        "color_bg": "#EFF6FF",
        "has_subsections": True,
        "subsections": {
            "global_indices": {
                "label": "Global Indices (India · US · HKEX · LSE)",
                "feeds": [
                    ("ET Markets", "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"),
                    ("LiveMint Markets", "https://www.livemint.com/rss/markets"),
                    ("CNBC Markets", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
                    ("Reuters Finance", "https://feeds.reuters.com/reuters/financials"),
                ],
            },
            "commodities": {
                "label": "Commodities & Precious Metals (Spot Gold/Silver LBMA)",
                "feeds": [
                    ("Metals Focus", "https://www.metalsfocus.com/rss"),
                    ("Investing.com Gold", "https://www.investing.com/rss/news_301.rss"),
                    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/marketpulse/"),
                ],
            },
            "crypto": {
                "label": "Crypto",
                "feeds": [
                    ("Finance Magnates", "https://www.financemagnates.com/cryptocurrency/feed/"),
                    ("Decrypt", "https://decrypt.co/feed"),
                    ("ET Crypto", "https://economictimes.indiatimes.com/tech/cryptocurrency/rssfeeds/103567081.cms"),
                ],
            },
            "cfds_margin": {
                "label": "CFDs & Margin",
                "feeds": [
                    ("Finance Magnates", "https://www.financemagnates.com/feed/"),
                    ("FXStreet", "https://www.fxstreet.com/rss/news"),
                    ("LeapRate", "https://www.leaprate.com/feed/"),
                ],
            },
        },
    },
    "ai": {
        "label": "AI",
        "icon": "🤖",
        "color": "#8B5CF6",
        "color_bg": "#F5F3FF",
        "has_subsections": False,
        "feeds": [
            ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
            ("VentureBeat AI", "https://venturebeat.com/ai/feed/"),
            ("MIT Tech Review", "https://www.technologyreview.com/feed/"),
            ("The Verge AI", "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"),
        ],
    },
    "companies": {
        "label": "Companies",
        "icon": "🏢",
        "color": "#F59E0B",
        "color_bg": "#FFFBEB",
        "has_subsections": False,
        "feeds": [
            ("TechCrunch", "https://techcrunch.com/feed/"),
            ("Crunchbase News", "https://news.crunchbase.com/feed/"),
            ("ET Companies", "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms"),
            ("FintechNews UAE", "https://fintechnews.ae/feed/"),
            ("Arabian Business", "https://www.arabianbusiness.com/rss/"),
        ],
    },
    "product": {
        "label": "Product",
        "icon": "🚀",
        "color": "#EC4899",
        "color_bg": "#FDF2F8",
        "has_subsections": False,
        "feeds": [
            ("Mind the Product", "https://www.mindtheproduct.com/feed/"),
            ("TechCrunch Apps", "https://techcrunch.com/category/apps/feed/"),
            ("Product Hunt", "https://www.producthunt.com/feed"),
            ("First Round Review", "https://review.firstround.com/feed"),
        ],
    },
}

ITEMS_PER_SUBSECTION = 3
ITEMS_PER_SECTION = 5
MIN_SUMMARY_WORDS = 80  # fetch article body if RSS summary is shorter

# ── Relevance keywords per subsection ─────────────────
SUBSECTION_KEYWORDS = {
    "wealth_management": {
        "invest", "fund", "portfolio", "market", "stock", "bond", "equity",
        "asset", "wealth", "mutual", "etf", "return", "interest", "capital",
        "financial", "economy", "gdp", "inflation", "rate", "banking",
        "dividend", "ipo", "growth", "earning", "saving", "retirement",
        "pension", "insurance", "tax", "income", "profit", "loss", "trade",
        "currency", "forex", "monetary", "fiscal", "hedge", "private equity",
    },
    "fintech_uae": {
        "fintech", "uae", "dubai", "abu dhabi", "digital", "payment",
        "bank", "startup", "tech", "mobile", "gulf", "difc", "adgm",
        "crypto", "blockchain", "api", "neobank", "wealthtech", "insurtech",
        "regtech", "open banking", "lending", "remittance", "transfer",
    },
    "funds_etfs": {
        "fund", "etf", "index", "portfolio", "bond", "yield", "asset",
        "manager", "ucits", "invest", "tracker", "passive", "active",
        "aum", "nav", "fee", "expense", "allocation", "rebalance",
        "dividend", "analyst", "monetary", "emerging market", "vanguard",
        "blackrock", "ishares", "benchmark", "mutual", "pension",
    },
    "global_indices": {
        "nifty", "sensex", "bse", "nse", "dow", "nasdaq", "s&p",
        "ftse", "hkex", "hang seng", "nikkei", "index", "market",
        "rally", "stock", "equity", "trading", "bull", "bear",
        "correction", "futures", "options", "lse", "cac", "dax",
    },
    "commodities": {
        "gold", "silver", "oil", "commodity", "crude", "metal", "lbma",
        "precious", "mining", "copper", "platinum", "palladium", "spot",
        "bullion", "barrel", "brent", "wti", "natural gas", "aluminium",
    },
    "crypto": {
        "bitcoin", "ethereum", "crypto", "blockchain", "defi", "nft",
        "token", "coin", "btc", "eth", "web3", "altcoin", "stablecoin",
        "binance", "solana", "ripple", "xrp", "mining", "wallet", "exchange",
    },
    "cfds_margin": {
        "cfd", "margin", "leverage", "forex", "fx", "spread", "broker",
        "derivative", "futures", "option", "contract", "retail trader",
        "prop trading", "liquidity provider", "mt4", "mt5",
    },
}

# Topics that should be blocked even if a keyword substring accidentally matches
SUBSECTION_BLOCKLIST = {
    "wealth_management": {
        "salary", "hybrid work", "career advice", "workplace", "employee benefit",
        "job offer", "negotiate benefit", "non-monetary", "dowry", "matrimonial",
        "divorce", "cricket", "bollywood", "film", "movie", "actor",
    },
    "funds_etfs": {
        "dowry", "matrimonial", "cricket", "bollywood", "non-monetary",
    },
    "global_indices": {
        "dowry", "matrimonial", "cricket", "bollywood",
    },
}


# ── Helpers ───────────────────────────────────────────
def get_entry_summary(entry):
    for field in ("summary", "description"):
        val = entry.get(field, "")
        if val:
            return val
    content = entry.get("content", [])
    if content:
        return content[0].get("value", "")
    return ""


def looks_like_nav(text):
    """Return True if text appears to be site navigation rather than article prose."""
    if not text or len(text.split()) < 8:
        return False
    first = text[:120]
    # Nav text has no sentence punctuation in first 120 chars and many camel/joined words
    return not re.search(r"[.!?,]", first)


def clean(text, max_words=None):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")  # &nbsp; -> regular space
    text = re.sub(r"\s+", " ", text).strip()
    if max_words:
        words = text.split()
        if len(words) > max_words:
            truncated = " ".join(words[:max_words])
            # Cut at last sentence boundary so summary ends cleanly
            last_end = max(truncated.rfind(". "), truncated.rfind("! "), truncated.rfind("? "))
            if last_end > len(truncated) // 3:
                return truncated[: last_end + 1].strip()
            return truncated  # no sentence break found — return without ellipsis
    return text


def is_relevant(title, summary, sub_key):
    """Return True if article is relevant to the subsection."""
    keywords = SUBSECTION_KEYWORDS.get(sub_key)
    if not keywords:
        return True
    text = (title + " " + summary).lower()
    # Hard block on clearly off-topic content
    blocklist = SUBSECTION_BLOCKLIST.get(sub_key, set())
    if any(bk in text for bk in blocklist):
        return False
    return any(kw in text for kw in keywords)


_BODY_SKIP = {
    "facebook", "twitter", "linkedin", "instagram", "newsletter",
    "subscribe", "copyright", "advertisement", "sign up", "log in",
    "read more", "also read", "click here", "follow us", "whatsapp",
    "telegram", "youtube", "print edition", "download app",
}


def fetch_article_body(url, max_words=200):
    """Fetch article page and extract clean paragraph text."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; MorningDigest/2.0)"}
        )
        with urllib.request.urlopen(req, timeout=7) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        # Strip non-content sections
        for tag in ("script", "style", "nav", "header", "footer", "aside", "menu", "figure"):
            raw = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", raw, flags=re.DOTALL | re.IGNORECASE)
        paras = re.findall(r"<p[^>]*>(.*?)</p>", raw, flags=re.DOTALL | re.IGNORECASE)
        texts, word_count = [], 0
        for p in paras:
            t = clean(p)
            words = t.split()
            if len(words) < 20:
                continue
            # Skip paragraphs with no sentence punctuation — likely nav/menu text
            if not re.search(r"[.!?,;]", t):
                continue
            t_lower = t.lower()
            # Skip navigation/social/boilerplate paragraphs
            if sum(1 for kw in _BODY_SKIP if kw in t_lower) >= 2:
                continue
            texts.append(t)
            word_count += len(words)
            if word_count >= max_words:
                break
        return clean(" ".join(texts), max_words=max_words) if texts else ""
    except Exception:
        return ""


def fetch_feeds(feeds, max_items, sub_key=None):
    # Phase 1: collect from RSS feeds with relevance filtering
    candidates = []
    for source_name, url in feeds:
        try:
            feed = feedparser.parse(
                url,
                request_headers={"User-Agent": "Mozilla/5.0 (compatible; MorningDigest/2.0)"},
            )
            for entry in feed.entries[:5]:
                title = clean(entry.get("title", ""))
                raw_summary = get_entry_summary(entry)
                full_summary = clean(raw_summary, max_words=200)
                # Discard nav-contaminated RSS content so body fetch takes over
                if looks_like_nav(full_summary):
                    full_summary = ""
                link = entry.get("link", "#")
                if not title:
                    continue
                if not is_relevant(title, full_summary, sub_key):
                    continue
                candidates.append(
                    {
                        "title": title,
                        "summary": clean(full_summary, max_words=50),
                        "full_summary": full_summary,
                        "link": link,
                        "source": source_name,
                        "_short": len(full_summary.split()) < MIN_SUMMARY_WORDS,
                    }
                )
        except Exception as e:
            print(f"  [Error] {source_name}: {e}")

    items = candidates[:max_items]

    # Phase 2: enrich short summaries by fetching article body in parallel
    to_enrich = [(i, it) for i, it in enumerate(items) if it["_short"] and it["link"] != "#"]
    if to_enrich:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(fetch_article_body, it["link"]): i for i, it in to_enrich}
            for fut in concurrent.futures.as_completed(futures):
                i = futures[fut]
                try:
                    body = fut.result()
                    if (
                        body
                        and not looks_like_nav(body)
                        and len(body.split()) > len(items[i]["full_summary"].split())
                    ):
                        items[i]["full_summary"] = body
                        items[i]["summary"] = clean(body, max_words=50)
                except Exception:
                    pass

    for item in items:
        item.pop("_short", None)
        if not item["full_summary"]:
            item["full_summary"] = "Full summary not available. Click 'Read Full Article' to read on the source site."
            item["summary"] = item["full_summary"]

    return items


# ── HTML builders ─────────────────────────────────────
def build_cards(items):
    if not items:
        return '<p class="empty-state">No articles available right now.</p>'
    cards = ""
    for item in items:
        summary_html = (
            f'<p class="card-summary">{html.escape(item["summary"])}</p>'
            if item["summary"]
            else ""
        )
        safe_link = html.escape(item["link"])
        safe_title = html.escape(item["title"])
        safe_source = html.escape(item["source"])
        safe_full = html.escape(item.get("full_summary", item.get("summary", "")))
        cards += f"""
            <article class="card" onclick="openArticle(this)" role="button" tabindex="0"
              data-title="{safe_title}"
              data-source="{safe_source}"
              data-summary="{safe_full}"
              data-link="{safe_link}">
              <span class="card-source">{safe_source}</span>
              <span class="card-title">{safe_title}</span>
              {summary_html}
              <span class="card-read-more">Read more →</span>
            </article>"""
    return f'<div class="cards-grid">{cards}\n          </div>'


def build_section_html(key, section, data):
    color = section["color"]
    color_bg = section["color_bg"]
    style = f'style="--section-color:{color}; --section-color-bg:{color_bg};"'

    if section["has_subsections"]:
        total = sum(len(v) for v in data.values())
        body = ""
        for sub_key, sub_config in section["subsections"].items():
            items = data.get(sub_key, [])
            body += f"""
          <div class="subsection">
            <h3 class="subsection-title">{html.escape(sub_config['label'])}</h3>
            {build_cards(items)}
          </div>"""
    else:
        items = data
        total = len(items)
        body = build_cards(items)

    return f"""
      <section class="section-block" id="{key}" {style}>
        <div class="section-header">
          <h2 class="section-title">{html.escape(section['label'])}</h2>
          <span class="section-count">{total} articles</span>
        </div>
        {body}
      </section>"""


def build_vocab_html(daily_terms):
    cards = ""
    for i, (term, definition) in enumerate(daily_terms):
        cards += f"""
        <div class="vocab-card">
          <p class="vocab-label">Term {i + 1} of {len(daily_terms)}</p>
          <h3 class="vocab-term">{html.escape(term)}</h3>
          <p class="vocab-definition">{html.escape(definition)}</p>
        </div>"""
    return f"""
      <section class="section-block" id="vocabulary" style="--section-color:#6366F1; --section-color-bg:#EEF2FF;">
        <div class="section-header">
          <h2 class="section-title">Vocabulary</h2>
          <span class="section-count">{len(daily_terms)} terms today</span>
        </div>
        <div class="vocab-grid">
          {cards}
        </div>
      </section>"""


def build_full_html(all_data, daily_vocab):
    sections_html = ""
    nav_links = ""

    for key, section in SOURCES.items():
        data = all_data.get(key, {} if section["has_subsections"] else [])
        sections_html += build_section_html(key, section, data)
        nav_links += f'<a href="#{key}">{html.escape(section["label"])}</a>\n      '

    nav_links += '<a href="#vocabulary">Vocabulary</a>'
    sections_html += build_vocab_html(daily_vocab)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Morning Digest — {html.escape(today_str)}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #F8FAFC;
      --surface: #FFFFFF;
      --border: #E2E8F0;
      --text-primary: #0F172A;
      --text-secondary: #475569;
      --text-muted: #94A3B8;
      --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
      --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
      --shadow-hover: 0 6px 20px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06);
      --radius: 12px;
      --section-color: #64748B;
      --section-color-bg: #F8FAFC;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--text-primary);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}

    /* Header */
    header {{
      background: #FFFFFF;
      border-bottom: 1px solid var(--border);
      padding: 16px 24px;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: var(--shadow-sm);
    }}
    .header-inner {{
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .header-logo {{
      width: 34px;
      height: 34px;
      background: #0F172A;
      color: #FFFFFF;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.5px;
      flex-shrink: 0;
    }}
    .header-title {{ font-size: 19px; font-weight: 700; color: #0F172A; letter-spacing: -0.4px; }}
    .header-date {{ font-size: 12.5px; color: var(--text-muted); margin-top: 2px; }}

    /* Navigation */
    nav {{
      background: #FFFFFF;
      border-bottom: 1px solid var(--border);
      padding: 0 24px;
      position: sticky;
      top: 69px;
      z-index: 99;
    }}
    .nav-inner {{
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      overflow-x: auto;
      scrollbar-width: none;
    }}
    .nav-inner::-webkit-scrollbar {{ display: none; }}
    .nav-inner a {{
      text-decoration: none;
      color: var(--text-secondary);
      font-size: 13px;
      font-weight: 500;
      padding: 13px 14px;
      white-space: nowrap;
      border-bottom: 2px solid transparent;
      transition: color 0.15s, border-color 0.15s;
      display: flex;
      align-items: center;
      gap: 5px;
    }}
    .nav-inner a:hover {{
      color: #0F172A;
      border-bottom-color: #CBD5E1;
    }}

    /* Main */
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 36px 24px 56px;
    }}

    /* Section */
    .section-block {{
      margin-bottom: 52px;
      scroll-margin-top: 120px;
    }}
    .section-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding-bottom: 14px;
      margin-bottom: 24px;
      border-bottom: 1px solid var(--border);
    }}
    .section-title {{ font-size: 18px; font-weight: 700; color: #0F172A; letter-spacing: -0.3px; padding-left: 12px; border-left: 3px solid var(--section-color); }}
    .section-count {{
      margin-left: auto;
      font-size: 11px;
      color: var(--text-muted);
      background: var(--bg);
      border: 1px solid var(--border);
      padding: 3px 10px;
      border-radius: 4px;
      font-weight: 500;
    }}

    /* Subsections */
    .subsection {{ margin-bottom: 28px; }}
    .subsection-title {{
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-muted);
      margin-bottom: 14px;
    }}

    /* Cards */
    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 18px 20px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 9px;
      transition: box-shadow 0.2s ease, transform 0.2s ease;
      cursor: pointer;
    }}
    .card:hover {{
      box-shadow: var(--shadow-hover);
      transform: translateY(-2px);
    }}
    .card-source {{
      display: inline-flex;
      align-items: center;
      font-size: 11px;
      font-weight: 500;
      color: var(--text-muted);
      border: 1px solid var(--border);
      padding: 2px 8px;
      border-radius: 4px;
      width: fit-content;
    }}
    .card-title {{
      font-size: 14.5px;
      font-weight: 600;
      color: #0F172A;
      line-height: 1.45;
      display: block;
    }}
    .card:hover .card-title {{ color: var(--section-color); }}
    .card-summary {{
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.65;
      flex: 1;
    }}
    .card-read-more {{
      font-size: 12px;
      font-weight: 500;
      color: var(--section-color);
      display: inline-flex;
      align-items: center;
      gap: 2px;
      margin-top: 2px;
      opacity: 0.85;
    }}
    .card:hover .card-read-more {{ opacity: 1; }}
    .empty-state {{ color: var(--text-muted); font-size: 14px; padding: 16px 0; }}

    /* Vocabulary */
    .vocab-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 20px;
    }}
    .vocab-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-left: 4px solid var(--section-color);
      border-radius: var(--radius);
      padding: 24px 28px;
      box-shadow: var(--shadow);
    }}
    .vocab-label {{
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--section-color);
      margin-bottom: 8px;
    }}
    .vocab-term {{ font-size: 17px; font-weight: 700; color: #0F172A; margin-bottom: 10px; letter-spacing: -0.3px; }}
    .vocab-definition {{ font-size: 13.5px; color: var(--text-secondary); line-height: 1.75; }}

    /* Footer */
    footer {{
      background: #FFFFFF;
      border-top: 1px solid var(--border);
      text-align: center;
      padding: 22px 24px;
      color: var(--text-muted);
      font-size: 12px;
      line-height: 1.6;
    }}

    /* Article Modal */
    .modal-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.55);
      z-index: 200;
      align-items: center;
      justify-content: center;
      padding: 20px;
      backdrop-filter: blur(2px);
    }}
    .modal-overlay.active {{ display: flex; }}
    .modal-content {{
      background: #FFFFFF;
      border-radius: 16px;
      padding: 40px 44px 36px;
      max-width: 700px;
      width: 100%;
      max-height: 82vh;
      overflow-y: auto;
      position: relative;
      box-shadow: 0 24px 64px rgba(0,0,0,0.22), 0 4px 16px rgba(0,0,0,0.10);
    }}
    .modal-close {{
      position: absolute;
      top: 18px;
      right: 22px;
      background: none;
      border: none;
      font-size: 22px;
      cursor: pointer;
      color: var(--text-muted);
      line-height: 1;
      padding: 4px;
      border-radius: 4px;
      transition: color 0.15s;
    }}
    .modal-close:hover {{ color: #0F172A; }}
    .modal-source {{
      display: inline-flex;
      font-size: 11px;
      font-weight: 500;
      color: var(--text-muted);
      border: 1px solid var(--border);
      padding: 2px 10px;
      border-radius: 4px;
      margin-bottom: 16px;
    }}
    .modal-title {{
      font-size: 20px;
      font-weight: 700;
      color: #0F172A;
      line-height: 1.45;
      margin-bottom: 20px;
      letter-spacing: -0.3px;
    }}
    .modal-divider {{
      height: 1px;
      background: var(--border);
      margin-bottom: 20px;
    }}
    .modal-summary {{
      font-size: 14.5px;
      color: var(--text-secondary);
      line-height: 1.8;
      margin-bottom: 32px;
    }}
    .modal-link {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #0F172A;
      color: #FFFFFF;
      padding: 11px 22px;
      border-radius: 8px;
      text-decoration: none;
      font-size: 14px;
      font-weight: 600;
      transition: background 0.15s;
    }}
    .modal-link:hover {{ background: #1E293B; }}

    /* Responsive */
    @media (max-width: 640px) {{
      header {{ padding: 12px 16px; }}
      nav {{ top: 61px; }}
      main {{ padding: 24px 16px 40px; }}
      .cards-grid {{ grid-template-columns: 1fr; }}
      .vocab-card {{ padding: 20px; }}
      .section-title {{ font-size: 17px; }}
      .modal-content {{ padding: 28px 20px 24px; }}
      .modal-title {{ font-size: 17px; }}
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-inner">
      <div class="header-logo">MD</div>
      <div>
        <div class="header-title">Morning Digest</div>
        <div class="header-date">{html.escape(today_str)}</div>
      </div>
    </div>
  </header>

  <nav>
    <div class="nav-inner">
      {nav_links}
    </div>
  </nav>

  <main>
    {sections_html}
  </main>

  <footer>
    <p>Auto-generated daily at 8:00 AM IST</p>
    <p style="margin-top:4px;">Sources: Economic Times · LiveMint · Bloomberg · TechCrunch · Crunchbase · FintechNews.ae · Arabian Business · Reuters · CNBC · CoinDesk · Cointelegraph · Kitco · BullionVault &amp; more</p>
  </footer>

  <!-- Article Modal -->
  <div id="article-modal" class="modal-overlay" onclick="handleOverlayClick(event)">
    <div class="modal-content">
      <button class="modal-close" onclick="closeArticleModal()" aria-label="Close">&times;</button>
      <span class="modal-source" id="modal-source"></span>
      <h2 class="modal-title" id="modal-title"></h2>
      <div class="modal-divider"></div>
      <p class="modal-summary" id="modal-summary"></p>
      <a class="modal-link" id="modal-link" href="#" target="_blank" rel="noopener noreferrer">
        Read Full Article &rarr;
      </a>
    </div>
  </div>

  <script>
    // Dynamically pin nav below header and set scroll-margin-top on sections
    function fixStickyOffsets() {{
      var headerH = document.querySelector('header').offsetHeight;
      var nav = document.querySelector('nav');
      nav.style.top = headerH + 'px';
      var offset = headerH + nav.offsetHeight + 8;
      document.querySelectorAll('.section-block').forEach(function(el) {{
        el.style.scrollMarginTop = offset + 'px';
      }});
    }}
    fixStickyOffsets();
    window.addEventListener('resize', fixStickyOffsets);

    function openArticle(card) {{
      document.getElementById('modal-source').textContent = card.dataset.source;
      document.getElementById('modal-title').textContent = card.dataset.title;
      document.getElementById('modal-summary').textContent = card.dataset.summary || 'No summary available.';
      document.getElementById('modal-link').href = card.dataset.link;
      document.getElementById('article-modal').classList.add('active');
      document.body.style.overflow = 'hidden';
    }}
    function handleOverlayClick(e) {{
      if (e.target === document.getElementById('article-modal')) closeArticleModal();
    }}
    function closeArticleModal() {{
      document.getElementById('article-modal').classList.remove('active');
      document.body.style.overflow = '';
    }}
    document.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape') closeArticleModal();
    }});
    document.querySelectorAll('.card').forEach(function(card) {{
      card.addEventListener('keydown', function(e) {{
        if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); openArticle(card); }}
      }});
    }});
  </script>

</body>
</html>"""


# ── Main ──────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Morning Digest — {today_str}")

    start = (day_of_year * VOCAB_PER_DAY) % len(VOCABULARY)
    daily_vocab = [VOCABULARY[(start + i) % len(VOCABULARY)] for i in range(VOCAB_PER_DAY)]
    print(f"Vocabulary: {', '.join(t for t, _ in daily_vocab)}")

    all_data = {}
    for key, section in SOURCES.items():
        print(f"\n[{section['label']}]")
        if section["has_subsections"]:
            all_data[key] = {}
            for sub_key, sub_config in section["subsections"].items():
                items = fetch_feeds(sub_config["feeds"], ITEMS_PER_SUBSECTION, sub_key=sub_key)
                all_data[key][sub_key] = items
                print(f"   -> {sub_config['label']}: {len(items)} articles")
        else:
            items = fetch_feeds(section["feeds"], ITEMS_PER_SECTION)
            all_data[key] = items
            print(f"   -> {len(items)} articles")

    html_content = build_full_html(all_data, daily_vocab)

    os.makedirs("docs", exist_ok=True)

    for path in ["index.html", "docs/index.html", f"docs/{now.strftime('%Y-%m-%d')}.html"]:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Written: {os.path.abspath(path)}")
