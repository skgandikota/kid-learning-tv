# Privacy

The app stores a salted parent PIN hash and recent login attempts in local SQLite.
Session cookies support parent sign-in. There is no microphone capture, cloud AI
service or child activity recording. Optional Piper speech is generated locally.

YouTube URLs are fetched only when an authenticated parent submits them.
The download contacts YouTube and its media CDN; normal IP/network information
is visible to those services. Downloaded files, chosen titles and job status are
stored locally under the videos folder. No browser cookies or accounts are
passed to the downloader. There is no automatic TV playback when a download ends.
The active playlist and TV playback reports stay in memory and are not history.
The Food time flag persists locally.

Quiz timing preferences persist locally. Active rounds, chosen answers and
progress stay in memory, not a child history. Only fixed public picture labels
are synthesized and cached as WAV files; no child speech is captured.
Optional voice setup contacts Hugging Face to download a pinned model on the
target laptop. Pictures are bundled locally and do not contact image hosts
during play. A browser fallback uses only voices marked as local/offline.

Existing stored files and old database tables are preserved during updates but
are not used unless part of the video library. Backups may contain those files.
Keep backups private. HTTP is unencrypted: use only a trusted home network.
