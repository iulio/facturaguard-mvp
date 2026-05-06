# UI Refresh v3.23

FacturaGuard v3.23 refreshes the main frontend layout.

## Changes

- normalizes `NEXT_PUBLIC_API_BASE`
- prevents double-slash calls like `//auth/register`
- improves login/register layout
- separates dashboard topbar from navigation
- adds responsive navigation pills
- improves card spacing, table readability and mobile behavior
- keeps existing app logic and API calls intact

## Railway note

`NEXT_PUBLIC_API_BASE` is bundled into the client during `next build`, so set it on the Railway frontend service before deploying/redeploying the frontend.
