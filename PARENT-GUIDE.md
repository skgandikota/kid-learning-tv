# Parent page

Open `http://<laptop-IP>:8765/parent` and enter your existing PIN.
After login, **Food time** is at the top. Tap it to show the meal-time image on
the TV; tap again to return to the Quiz home tile. A green button means it is on.
You can also sign out. Signing out does not change the TV.

Food time shows only the image, with no clock or controls. No microphone is used.

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

During video, the TV has no buttons: just video, a small total countdown and a progress bar.
The countdown includes all selected videos and stops decreasing during pauses
and buffering. After the last one, the screen-time-finished picture appears.
Stop returns to the Quiz home tile. Food time cancels playback and shows its image.
Refreshing the TV resumes the active video at its last reported position;
restarting the service ends the playlist instead of starting it again.

## Picture quizzes

Your child can click **Quiz** on the TV, then a large picture category. The red
**X** at the top closes the quiz, including the category menu and finished screen.
This button appears only in quizzes, never over Food time or videos.

On your phone, open **Quiz**. Choose seconds to guess (5/10/15/20), up to five or
ten pictures, and ticking on/off. **Save for next round**, then choose a category.
Each round uses different randomly selected pictures without repeats.
The clock waits until the picture loads. The answer then appears and is spoken,
staying at least four seconds and waiting for speech before the next picture.
Pause, Resume, Show answer, Next, Categories on TV and Close quiz work remotely.
Quiz settings persist; the active round does not resume after a service restart.

For age three, start with animals, fruits or favourite car logos: five pictures,
ten seconds each. Say answers together; the app does not listen, score or mark
answers wrong. Birds and vegetables add variety. Country shapes are harder;
flags are an optional matching game rather than a test.

The voice status explains whether Piper natural speech or basic eSpeak fallback
is available. If both fail, the TV attempts an installed offline browser voice;
otherwise it still shows the name and reports a sound warning here.
Check laptop volume and kiosk autoplay if speech cannot play. A picture-loading
warning also appears here; use Next or restart the category.
