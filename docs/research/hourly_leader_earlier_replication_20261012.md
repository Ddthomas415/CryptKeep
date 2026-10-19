# Earlier hourly replication: positive candidate, not certified edge

ENGINEER stage, READY_FOR_INDEPENDENT_REVIEW. Original accepted recent study
unchanged. One selected arm only:20%closingpeakdip,5%entrytarget,48hourtimeout,
72hourdipwait, nextopenentry/exit,50bpsfee+25bpsadversepriceeachside.

## Data and provenance

Used existing coinbase_hourly_last60d.tar.xz; archive checksum and all395hourly
input member checksums matched the published manifests. Read members directly,
no tar extraction/path writes. Plan frozen before adaptation was evaluated.
Earlier evaluation Aug11 00:00UTC to Sep30 17:00UTC exclusive. Later study begins
Sep30 17:00UTC, so hourlyevaluationwindows do notoverlap. Newperiod still belongs
to alreadyexploredhistoricalarchive; NOTuntouchedholdout. UnderlyingcurrentOct9
universe395products differs fromlater403marketcatalogue; historicalflagsunknown.
Only165-301markets/hourrankable under25barcontiguity andpositivevolumechecks.

## Economic result

202distinctsymbol/entry pairs,191closes,137netpositivecloses. Meanclosednet
+USD20.23perUSD1000scenario. Including11unresolvedlastmarks:mean+USD14.32.
Worst primaryclosednetloss -USD493.11. These are modeled events, not a portfolio.
Everyevent/status retained. Originalprimary repeatedentryview878entries840closes
mean+USD17.09; correlated repetitions must not become an effective sample size.

MDT supplies49.23% of aggregate distinctentrynetplusmarks. RemovingMDT entirely
leavesmean+USD7.57; removingtopthreecontributors leaves+USD2.57. These exclusions
are posthocfragilitychecks, notnewentryrules orstatisticalproof. Removingbestcoin
fromrecentcandidate still leaves+USD30.90perdistinctentrymarkedscenario.

Sevenearlierunresolvedlastmarks andthreerecentlastmarks arestale. Treatingthe
staleearlierpositions asworthless changesmarkedmean to-USD17.67; samerecentscenario
changes+USD37.48 to-USD13.56. These are extreme sensitivity assumptions, NOT
observedlosses orcurrentvaluations. No commoncutoffNAV or executionproof exists.

Therefore: same frozen arm producedpositiveexploratorysamples across two
nonoverlappingwindows, even afteridenticalentrycollapse andbestcoinremoval.
That justifies preserving it as a researchcandidate, NOT buying it live.
Statisticaldependence, multiplearmselection, staleunknownpositions, missing
rankablemarkets and assumedcosts remain unresolved. No source tuning performed.

## Artifacts and checks

Adapter scripts/research/replicate_hourly_leader_archive.py;
research/hourly_leader_earlier_plan/raw/results_20261012.json;
research/hourly_leader_earlier_dependency_audit_20261012.json. Adapter checksum
bound inplan, base source/dataset bound by accepted analyzer. Existingtargeted
six-test slice verified forrecentstudy; no new standaloneadaptertests yet.
SeparateFaradayreviewrequested foradaptation andinterpretation.
Inherited first6day/last6day resultfield names do NOT describe thislongerperiod:
firstcohort isfirst6days,secondisallremainingdays. Those fields are not cited as
independentvalidation; onlyallperiodstatistic used. No new tuning/thresholds.
No account/liveorders/risk/config/jobs/collectorchanges. Reviewpending.

## Separate GATE outcome and provenance clarification

Faraday acceptedboundedhistoricalreplication ACCEPTED_WITH_RISK. Independently
reconstructed441755adaptedcandles,1217events andallartifact/calculationbindings;
archive and395inputmemberhashesmatch. No blockingcausality/arithmetic defect.

The adapter inherited registered_utc fromtherecentplan. Thatfield is NOT this
replication's registrationtime and mustnot supportnewpreregistrationclaim.
Save-before-analysis order is shownincode; independenttimestamp chronology is
UNVERIFIED. Preservefrozenfiles; thisaddendumcorrectsinterpretation only.
Legacycohortlabelissue retained/disclosed andnotusedasindependentvalidation.
Seven earlierunresolvedmarks are149-1138hours stale. +USD14.32markedmean is
NOTendpointprofit/currentNAV. Permittedclaimonly: unchangedselectedarmpositive
exploratorymodeledsummaries intwononoverlappinghistoricalwindows. No certified
edge/holdout/executableprofitability/portfolio/trading/promotion authorization.
