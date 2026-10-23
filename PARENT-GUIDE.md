# Parent page

Open `http://<laptop-IP>:8765/parent` and enter your existing PIN.
After login, **Food time** is at the top. Tap it to show the meal-time image on
the TV; tap again to return to the blank screen. A green button means it is on.
You can also sign out. Signing out does not change the TV.

Food time shows only the image, with no clock or controls. There are no games,
microphone capture or AI features.

## Video

Open **Video** beside Food time. At the top, enter a YouTube URL and a title, then
tap **Download in background**. Only download videos you own or have permission
to download. Progress and failures appear here; a completed video joins the
library but does not play automatically.
One download runs at a time, up to 2 GiB per video. Live streams, playlists,
login-required or restricted content are not supported. If the app restarts,
an unfinished download is marked failed; submit it again to retry.

The fixed laptop folder is `/var/lib/kid-learning-tv/videos`. Compatible local
MP4, M4V and WebM files copied there also appear. Files must be readable by the
`kid-learning-tv` service account. Files that cannot play show an error.
Supported video codecs are H.264, VP8, VP9 and AV1, with AAC, Opus, Vorbis or MP3
audio. Actual decoding depends on the TV browser; H.264/AAC MP4 is preferred for
this laptop. Merging a download can temporarily need extra disk space.

Select videos one by one in the required order; the selection numbers and list
show 1, 2, 3... Tap **Play selection**, or use **Play** beside a single video.
The **On TV** list shows the active order and highlights the current video.
All pause/resume, stop, previous/next, seek, volume and mute controls stay here.
Playback errors, buffering and missing TV connection are reported here too.

The TV has no buttons: just video, a small total countdown and a progress bar.
The countdown includes all selected videos and stops decreasing during pauses
and buffering. After the last one, the screen-time-finished picture appears.
Stop returns to black. Food time cancels playback and shows its image.
Refreshing the TV resumes the active video at its last reported position;
restarting the service ends the playlist instead of starting it again.
