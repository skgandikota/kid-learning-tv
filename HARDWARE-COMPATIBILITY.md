# Hardware compatibility (preliminary)

The app is a small Python/Flask local web application and can run on a supported 64-bit Linux computer capable of running Lubuntu and a modern browser. A TV can be used as the display through the computer's video output; parent controls can be reached from another device on the same trusted LAN.

This repository does not establish tested CPU/RAM/storage minimums, GPU acceleration requirements, or a verified list of TV, remote, touchscreen, audio, or microphone models. Hardware compatibility is therefore **unverified**. A microphone is not needed or used by the current app. Optional local eSpeak NG requires its OS package and a working audio output device.

For lower-resource systems, begin with `config/very-low-resource.json` and adjust display/browser settings. Test the actual machine, resolution, audio path, Wi-Fi reliability, and browser media support before placing it in child use. Do not infer that a device is certified from this guide.
