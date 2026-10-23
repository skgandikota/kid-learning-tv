# Third-party software and licensing

This project directly declares Flask 3.1.2 and jsonschema 4.25.1 in `pyproject.toml`; `requirements.lock` is also part of the deployment. The deployment installer additionally requests waitress as a production WSGI server because it is not currently declared in the project manifest. Exact transitive dependency versions are determined by the lock/install environment.

| Component | Use | License reference |
|---|---|---|
| Flask | Local web framework | BSD-3-Clause; see the installed package metadata |
| jsonschema | Content/schema validation | MIT; see the installed package metadata |
| waitress | Optional production WSGI server installed by deployment script | ZPL-2.1; see the installed package metadata |
| qrcode | Optional QR generation for the parent connection page; not installed by deployment script | Consult installed package metadata for the selected release |
| eSpeak NG / eSpeak | Optional system-provided local TTS | Consult the distribution's package copyright/license notices |
| Python, SQLite, Lubuntu, Chromium/Chrome | Runtime/platform/browser, not bundled here | Consult each distribution/vendor's notices |

This page is an inventory, not a reproduction of third-party license texts or a complete SBOM. Before redistribution, generate and review an inventory for the exact installed versions, preserve their copyright/license notices, and inspect licenses for transitive dependencies and any media/assets included in the release.

The learning library contains original browser implementations of common counting,
colour/shape matching and matching-pairs games. GCompris is an inspiration, not a
bundled dependency: none of its source code, artwork, audio or activities is included.
