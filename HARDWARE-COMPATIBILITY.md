# Hardware compatibility (preliminary)

The app is a small Python/Flask local web application and can run on a supported 64-bit Linux computer capable of running Lubuntu and a modern browser. A TV can be used as the display through the computer's video output; parent controls can be reached from another device on the same trusted LAN.

This repository does not establish tested CPU/RAM/storage minimums, GPU acceleration requirements, or a verified list of TV, remote, touchscreen, audio, or microphone models. Hardware compatibility is therefore **unverified**. Optional voice play uses the laptop microphone through Chromium on localhost, Vosk's small English model (approximately 40 MB download / 300 MB runtime RAM), and eSpeak NG. Recognition of a young child's voice and usable microphone distance must be checked on the actual laptop. Card matching requires tap/click rather than spoken input.

For lower-resource systems, begin with `config/very-low-resource.json` and adjust display/browser settings. Test the actual machine, resolution, audio path, Wi-Fi reliability, and browser media support before placing it in child use. Do not infer that a device is certified from this guide.
