# Recovery directory-entry screening correction

Date2026-10-18. ENGINEER stage. Actual copy remains INCOMPLETE; first partial
directory is retained unchanged. No second copy has run at this point.

Separate root-entry review c9bec95d... rejected sourceca410362... because the ZIP
`is_dir()` filename test alone did not validate stored type, encryption or payload
before skipping a root entry. TAR empty-root crash handling itself was addressed.

Correction: ZIP root metadata is skipped only for an explicitly stored directory,
zero payload and no encryption flag. Symlink, regular-file, encrypted or payload
root entries are refused. Nonroot ZIP directories and all TAR directories with
payloads are also refused; no directory label can silently hide file data.
Safe empty TAR/ZIP roots and their contained public data retain bounded screening.
No source allowlist, credential denial or path/restore criterion is relaxed.

Focused synthetic selection39passed0.49s, exit0. One intermediate test collection
syntax error was corrected before this final run; it was not a passing result.
Source SHA2568efaf5fc4e3ff508640fb038d6d2b1f74c7a30ece9ef1233449f491f051655a9;
tests281bf5be9942502c8801fda2216be1754303af7444a33e171c3eca247a301c60.

Corrected source is READY_FOR_INDEPENDENT_REVIEW for the same ongoing approved
local recovery objective and fresh `_r2` sibling destination. Prior failure and
reviews are preserved; no automatic retry, cleanup, source data alteration,
publication, Git mutation, credentials, accounts or runtime action is included.
