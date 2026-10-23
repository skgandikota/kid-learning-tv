# Test report

`python -m pytest -q`: **13 passed** on Windows.

Covers blank TV markup, login/logout, invalid PINs, CSRF rotation, rate limiting,
localhost-only first setup, existing PIN/data preservation and removed endpoints.
Python compilation and parent JavaScript syntax checks passed.
Headless Edge confirmed a black empty TV, phone-sized login, refresh persistence
and sign-out. Deployment shell syntax checks passed.

Target Lubuntu service operation still needs confirmation after updating.
