# Test report

`python -m pytest -q`: **14 passed** on Windows.

Covers blank TV markup, login/logout, invalid PINs, CSRF rotation, rate limiting,
localhost-only first setup, existing PIN/data preservation and removed endpoints.
Python compilation and parent JavaScript syntax checks passed.
Headless Edge confirmed a black empty TV, phone-sized login, refresh persistence
and sign-out. Deployment shell syntax checks passed.

Food time checks cover parent authentication, CSRF, invalid input, on/off state
and persistence across app restart. Separate real Edge TV and phone-sized pages
confirmed live switching, image loading, no TV buttons/text/cursor, no scrolling,
refresh persistence and return to black at 1920x1080, 1366x768 and 1024x768.
The supplied image is fitted without cropping; nonmatching aspect ratios have
black bars. No clock was added. No browser JavaScript errors were observed.

Target Lubuntu service operation still needs confirmation after updating.
