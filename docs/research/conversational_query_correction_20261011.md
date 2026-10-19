# Ordinary Questions, Explicit Search Trace

The demonstrated miss was a full-question conjunction, not unavailable data:
`What news explains Bitcoin liquidations?` returned no clean-archive matches,
while `Bitcoin liquidations` returned relevant documents.

The bounded correction removes conversational scaffolding only for supported
question prefixes. It does not OR all words, add synonyms, interpret dates or
claim semantic understanding. Explicit syntax, negation, numeric questions and
topical words remain preserved. `news` is removed only from the specific opening
`what/which news explains`, not from topics such as fake news.

Memory exposes the original and normalized query, method and preservation mode;
tools and explanation metadata retain that trace. Existing asset/time/archive
integrity guards remain intact. No paid model, migration, strategy or collector.

The fixed verification contract is conversational_query_contract_20261011.json.
Its examples diagnose known failures, not general semantic accuracy. Unit and
route tests total 68 passing cases (96 existing framework warnings).
Independent source/operator review and deployed proof are recorded in the work
log. No financial simulations or frozen candidates are rerun for this correction.
