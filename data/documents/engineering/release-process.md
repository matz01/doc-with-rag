# Release Process

*Owner: Engineering*

## Release train

- We release to production **every two weeks, on Tuesday**.
- Unfinished features ship behind **feature flags**.
- The release branch is cut on the **Friday before** the release.

## Deployment windows

- Production deployments happen between **10:00 and 16:00 CET**.
- **No deployments on Friday after 14:00.**
- Every deployment must be rollback-ready; the target rollback time is **15 minutes**.

## Change freeze

There is a change freeze from **15 December 2026 to 7 January 2027**. Only hotfixes are allowed during the freeze.

## Hotfixes

A hotfix needs **two approving reviews** and approval from the **Engineering Manager on duty**. It must be followed by a regular fix in the next release train.
