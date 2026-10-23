# Privacy

The app stores a salted parent PIN hash and recent login attempts in local SQLite.
Session cookies support parent sign-in. There is no microphone capture, AI,
cloud AI service or activity recording in this version.

YouTube URLs are fetched only when an authenticated parent submits them.
The download contacts YouTube and its media CDN; normal IP/network information
is visible to those services. Downloaded files, chosen titles and job status are
stored locally under the videos folder. No browser cookies or accounts are
passed to the downloader. There is no automatic TV playback when a download ends.
The active playlist and TV playback reports stay in memory and are not history.
The Food time flag persists locally.

Existing stored files and old database tables are preserved during updates but
are not used unless part of the video library. Backups may contain those files.
Keep backups private. HTTP is unencrypted: use only a trusted home network.
