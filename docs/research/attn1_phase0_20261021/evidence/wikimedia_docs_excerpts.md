# Wikimedia documentation excerpts (fetched 2026-10-21 about 21:30 UTC, read-only)

## Analytics API access policy
Source: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html
> Terms of use ​ By using the API, you agree to Wikimedia's terms of use and privacy policy ...
> Data licensing ​ Data provided by the API is available under the CC0 1.0 license
> Client identification ​ The API requires an HTTP User-Agent header for all requests. This helps identify your app and ensures that system administrators can contact you if a problem arises. Clients making requests without a User-Agent header may be blocked without notice.
> Rate limits ​ Rate limits are dependent on the client's identity and level of access. See Wikimedia APIs/Rate limits . Your client may be blocked if you endanger the stability of the service. To stay within a safe request rate, wait for each request to finish before sending another request.

## Page view concepts
Source: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/concepts/page-views.html
> Redirects, particularly redirects based on alternate spellings of a page title, aren't counted as views of the actual page.
> Page views associated with user agents that self-identify as bots receive the spider category. Other automated traffic, identified as such based on a set of heuristics, receives the automated category instead.

## Page view reference
Source: https://gitlab.wikimedia.org/repos/generated-data-platform/aqs/analytics-api/-/raw/main/reference/page-views.md
> These endpoints serve data starting on July 1, 2015.

## Per-article endpoint (OpenAPI spec)
Source: https://wikimedia.org/api/rest_v1/metrics/pageviews/api-spec.json
- path: `/pageviews/per-article/{project}/{access}/{agent}/{article}/{granularity}/{start}/{end}`
- agent enum: ['all-agents', 'user', 'spider', 'automated']
- access enum: ['all-access', 'desktop', 'mobile-app', 'mobile-web']
- granularity enum: ['daily', 'monthly']

## Changelog
Source: https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/changelog.html
- 2020-04-29: "Added the automated agent type for page views identified as bots based on a set of heuristics", as opposed to the spider type, which identifies bots by user agent.

## Rate limits (new in 2026, "subject to experimentation and change")
Source: https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits (raw wikitext)
- Unidentified requests (no identifying characteristics other than IP address): 10 requests/min.
- Unauthenticated bot requests with a compliant User-Agent: 200 requests/min.
- Best practice: a User-Agent "that includes contact information such as an email or full URL"; at most 3 concurrent requests; respect Retry-After on 429.

## Wikidata Query Service, observed 2026-10-21 (time in requests.log)
- A label-matching SPARQL request returned HTTP 429 "Aggressively rate-limiting to 1 req / min - this rule was created during active wdqs outage". It was not retried.
