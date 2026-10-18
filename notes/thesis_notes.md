# notes: method choices + what the results mean

numbers are in 03_gold / results/, this is only the why and the reading.
TT = TikTok


## method (ch 3): what I chose and what I didn't

**TT + X instead of many platforms**
Kaushal 24, Trujillo 25, Groesch 26 all compare 6-8 platforms at aggregate level -> can't isolate anything that way.
careful: don't sell it as "max video vs text contrast". X has no text in the data at all (99.995% synthetic media), TT is 55% text. that's why modality is looked at inside TT.

**SoR database, not the transparency reports**
reports are aggregate, half-yearly, every platform defines its own stuff (Urman & Makhortykh 23).
TT's own report counted one item under every violated policy until H2 2025 (TT additional doc, section 2). the DB doesn't do that.

**describe + compare periods, no significance tests**
824M rows -> basically every difference is "significant", p-values say nothing. so effect sizes (ratios, pp).
regression like Groesch 26 makes no sense with 2 platforms.
methods source: Lin, Lucas & Shmueli 2013 ("too big to fail", ISR 24(4), 906-917), in literature/ now. abstract p. 906: in very large samples p-values go quickly to zero, relying on them alone can mean claiming results of no practical significance.

**Germany = DE in territorial_scope, not the DE-only rows**
DE-only = 1.69M rows (0.2%) and it's a different population: 66% OTHER content type, almost no images, the civic cat. shows up 251 times.
P&V 25: 99% of decisions apply EEA-wide anyway.
-> DE-only check is inconclusive, not negative. report it like that.

**shares, not counts**
TT volume more than doubles Jan -> Mar for reasons that have nothing to do with the election.
not per AMAR either: P&V use AMAR to compare countries. RQ2 compares a platform with itself over time, so its own total is the denominator.

**weekly**
X has ~730 statements/day, daily is too noisy (CV 0.33 in April). monthly = 6 points, useless for before/after.
both platforms have weekday effects, weeks remove them.

**granularity = number of filled optional fields**
not "quality of the free text": TT decision_facts has 7 distinct values. nothing to analyse there.
strict count is the main one, because the conditional fields depend on decision_ground and X/TT use different grounds.

**campaign window**
the periods in tab 6 were set after looking at the data (jump on 20 Jan). circular, can't carry the result alone.
independent window: dissolution of the Bundestag (27 Dec 24) to election day -> 1 Jan-23 Feb in my data.
5.41% vs 2.97% in May-Jun = 1.82x (tab 6b). still holds. need a source for the dissolution date.

**application_date as time axis**
like Trujillo 25, Groesch 26, Shahi 25. hardly matters here: 96% of TT is decided the same day it's posted, X always.


## results -> what they mean (ch 5)

**automation is the other way round than Gorwa 20 expects**
speech 98.8%, elections 99.2% automated vs porn 59%, minors 41.6%. by type: text 99.2 > video 93.3 > image 89.5 (fig 2).
Gorwa: visual/hash stuff should be the most automated. it's the least.
my reading: automation follows how bad a mistake would be, not how easy detection is. sensitive cats go to humans even where classifiers exist.
fits gatekeeping: selection criteria follow what the org wants (Wallace 17, Klonick 18).
speculative! I can't see why a case went to a person. -> this is my open tension for ch 5, leave it open.

**text > video > image**
maybe TT "text" is mostly comments, done with keyword matching. also speculative.
careful: the category mix is different per content type, so it's not clean.

**more automation = less detail? (H1)**
inside TT: 1.003 fields automated vs 1.115 manual (tab 11). right direction but basically nothing.
TT reports sit at the schema minimum no matter who decides -> the detail is set by the reporting pipeline, not by who decides. that's the disclosure gate from 2.4.
don't call it a correlation, 2 platforms.

**the rise during the campaign (H2)**
1.82x with the independent window.
starts exactly on 20 Jan. same day as the US inauguration, 2 days after TT went dark in the US. in DE: Aschaffenburg 22 Jan, Bundestag migration vote 29 Jan. (check all dates + find sources)
the category is applied almost only EEA-wide (251 DE-only vs 37.3M) -> the DB can't tell whose politics drove it.
so: "rise during the campaign, cause can't be attributed". NOT "TT reacted to the election".
fits Zimmer 26 (attribution problem) and my own point in 2.1. it's a limit of the DB, which is kind of my whole argument anyway.

**it doesn't stop at the election**
post-election 5.74% is even higher than the campaign window 5.41%. back to baseline only in April/May.
H2 says "transient": it is, but the peak isn't at the event, it outlasts it.

**more content or stricter moderation?**
can't separate them, I only see what got moderated.
Solovev 26 (25k German political TT videos) makes "more content" plausible. not proven. -> limitation.

**automation flat at ~96%**
ceiling, it can't really go higher.
the granularity part of H2 was derived from "pressure -> more automation". automation didn't move, so that part never kicks in. write both as one result, not two separate rejections.

**it's an image thing**
96% of the civic cat. is image content. within images 40% -> 61% in the campaign (fig 5).
-> the event effect depends on modality (affordances + agenda-setting together).
but: the cat. is 40-48% of TT's image moderation even outside the election. TT uses it as a standing image category. and TT mapped its own labels onto the DSA categories (add. doc, section 2). so wording: "civic-discourse and elections category", never "election content".

**politics gets demoted, not removed**
in the category ~90% "not recommended", only ~9-18% removal. overall ~60% removal.
campaign didn't change it (10.5 -> 9.1%, and the two baselines disagree: 10.5 vs 17.7) -> no event effect, just drift.
soft gate: Zeng & Kaye 22 (visibility moderation), Donohue via Wallace (shaping/display).
maybe: Horta Ribeiro 23 found hiding (not deleting) comments had small, insignificant effects on later rule-breaking. so the soft gate might deter less. careful, that's Facebook comments, not TT images. speculative.

**X: nothing in the category**
0 statements in 6 months. narrow disclosure gate or really no moderation? can't tell (disclosure posture, 2.1).
X also says ~0% automated while its own transparency report says it uses automation (Trujillo 25, Shahi 25, Groesch 26) -> limitation, self-reported data.

**one law, two records**
the fields barely overlap: X fills illegal_*, TT fills incompatible_* (fig 4). measure types barely overlap (fig 3). X drops category_specification after June.
-> the DB can't carry the cross-platform comparison it was built for (Groesch 26, Trujillo 25).

**TT decision_facts = one sentence**
7 distinct values, 97.25% is "The decision was taken pursuant to own-initiative investigations."
Kaushal 24 said explanations are vague, this puts a number on it. Art. 17(3)(b) DSA asks for the facts and circumstances.

**X names no measure in 26.4%**
just "Nsfw", no restriction stated. Art. 17(3)(a) wants the type of restriction.

**X "gap" in March/April**
not missing data. X just submitted 15-23 days late (17 Apr-1 May). all days are there. not a coverage limitation, at most a small timeliness point.
