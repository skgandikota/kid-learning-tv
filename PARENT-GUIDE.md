# Parent page

Open `http://<laptop-IP>:8765/parent` and enter your existing PIN.
After login, **Food time** is at the top. Tap it to show the meal-time image on
the TV; tap again to return to the Quiz home tile. A green button means it is on.
You can also sign out. Signing out does not change the TV.

**Home** stops the current activity and returns the TV to its game choices.
**Clock** stops the activity and shows only a large digital clock on black.
It uses the TV laptop's local time in 24-hour format. No buttons or cursor
appear on the TV; use **Home** on your phone to leave the clock.

**Move back** shows a friendly child-and-TV picture with "A little step back!"
and "Let's watch from our comfy spot."
**Painting time** shows the supplied painting picture with "It's painting time!"
Both stop the current activity and stay on the TV until you choose Home or
another activity. There are no child buttons, cursor or sounds. A TV page
refresh keeps the screen; a service restart returns home.

**Refresh TV** reloads the TV page remotely without clearing the current
activity. Games keep their progress; video resumes near its last reported
position. It needs the TV page to be open and connected; it cannot reopen a
closed browser or fix a frozen browser. Refresh the TV manually once after
installing the version that first adds this button.

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
**Everyday words** (25 words). Each character uses its parent-supplied picture
on both the choice card and inside the lesson. Flash is the first choice; other names
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
After the full-name announcement finishes, the next lesson starts automatically.
Large left/right arrows in the bottom corners go back or forward at any time,
even before finishing a name or while it is speaking. Switching cancels the old
audio and starts the chosen lesson afresh; the first/last ends return to choices.
Lessons move through the names and then Ant, Apple, Cat, Dog, Pig,
Hen, Duck, Fish, Table, Chair, Bed, Cup, Book, Ball, Head, Hair, Eye, Ear,
Nose, Mouth, Tooth, Hand, Foot, Arm and Leg. Everyday words have matching pictures.
**Hear again** repeats the introduction, or the completed
name. **Choose a name** returns to choices; the red X returns home.

Sounds are local, synthesized British-English approximations, not human
recordings. Phonics uses eSpeak NG with short vowel-assisted releases for
voiced stops such as B/D/G/J because its bare consonants are silent.
Listen together and model the sounds yourself; this is playful practice, not a
validated reading course. The existing Piper/basic voice speaks the full names.
Sound failures are shown explicitly; the app does not substitute letter names
for missing phonics. Rerun the laptop update and check volume/kiosk autoplay.

## Adventure games

Click **Adventure games** on the TV and choose a picture.
All seven games have spoken instructions, large choices and a red X.
There are no timers, scores, penalties or microphone recording.

| Game | How to play |
|---|---|
| Hero Rescue | Click the requested number of puppies; each rescue is counted aloud. |
| Feed the Monster | Feed the friendly monster the requested colour, fruit or vegetable. |
| Build a Hero Vehicle | Pick shapes to add wheels, a body, a window and a flag; watch it drive away. |
| Who's Hiding? | Use a silhouette and a spoken clue to find an animal; correct choices reveal it. |
| Pack the Adventure Bag | Remember the displayed items; they hide before you choose what to pack. |
| Finish the Magic Path | Look at the picture sequence and choose what comes next. |
| Silly Body Robot | Add eyes, a mouth, arms and legs; count paired parts and watch the completed robot dance. |

Wrong choices leave the challenge unchanged and give a gentle hint. Finished
challenges move on after their spoken celebration. **Hear again** repeats
instructions; in the bag game it shows the memory items again and restarts packing.
**Ready to pack!** can hide the memory pictures when your child is ready.
**Next adventure** moves on after a completed challenge; **Play again** restarts
the game when its short set is done.

On your phone, sign in and open **Adventures**. You can start a game, show the
game menu or close adventures. Set counting to **3 or 5**, memory to **2 or 3**
items, turn spoken instructions off/on, and choose which games appear.
Press **Save adventure settings**. Defaults are counting to three, two-item
memory and all seven games enabled with speech.
Difficulty/speech changes apply to the next game; disabling the active game
closes it immediately. Parents can interrupt with Food time, a video or a quiz.
Active games resume on TV refresh, but close when the service restarts.

Refresh keeps the current name and progress. Closing, Food time, a video or
service restart ends the activity. No typed text or mistakes are recorded.
