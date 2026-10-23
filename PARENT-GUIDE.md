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

## Card match

On the TV home, click the two smiling cards labelled **Card match**.
Find pairs of familiar animals, fruits and birds. Matching cards disappear with a
gentle magical sound; different cards stay visible briefly, then flip back.
Only two cards can open at once. There is no time limit, scoring or wrong-answer
sound. Complete each board to move through 20 rounds: 4, 6, 8, 10...42 cards,
adding two cards each round. Larger boards use more columns to stay on screen.
After round 20, choose Play again or the large red X to return home.
The later boards are deliberately harder; the red X is available at any time.

TV refresh keeps the current board; closing or restarting the service ends it.
Food time or a parent-started video interrupts and clears the game.
The white pointer is larger on home, quiz and matching screens, including
over buttons, but stays hidden during Food time, video and the end photo.
This changes only the website pointer, not Chromium's toolbar or the desktop.

## Hero Typing - Level 1

Click **Hero Typing** on the TV. Choose from **Heroes & friends** (26 names) or
**Everyday words** (eight short words). The character pictures are original
generic hero icons, not official artwork. Flash is the first choice; other names
include Batman, Superman, Wonder Woman, Robin, Aquaman, familiar Avengers,
Thanos, Joker, Venom, Woody and Buzz Lightyear. This is a starter collection,
not every Avengers character.

The introduction says and spells the name. A standing hero appears on the left;
letters and a large keyboard appear beside it. Type on the physical keyboard
or click the highlighted key. Lowercase and uppercase both work; spaces are
automatic. A different letter gets a gentle hint, not a buzzer or penalty.
Wait while each sound plays before typing the next highlighted letter.

Flash builds the sounds F, FL, FLA and FLASH. **SH** is one sound: S alone does
not play an incorrect sound; H completes the group. TH, CK and other letter
teams work similarly. Some character names are irregular or advanced: those
use sound chunks and the complete name, not invented blends at every letter.
Iron is treated as a special whole-word chunk.

After finishing, the hero celebrates and the full name is spoken.
**Next adventure** moves through the names and then Ant, Apple, Cat, Dog, Pig,
Hen, Duck and Fish. **Hear again** repeats the introduction, or the completed
name. **Choose a name** returns to choices; the red X returns home.

Sounds are local, synthesized British-English approximations, not human
recordings. Phonics uses eSpeak NG with short vowel-assisted releases for
voiced stops such as B/D/G/J because its bare consonants are silent.
Listen together and model the sounds yourself; this is playful practice, not a
validated reading course. The existing Piper/basic voice speaks the full names.
Sound failures are shown explicitly; the app does not substitute letter names
for missing phonics. Rerun the laptop update and check volume/kiosk autoplay.

Refresh keeps the current name and progress. Closing, Food time, a video or
service restart ends the activity. No typed text or mistakes are recorded.
