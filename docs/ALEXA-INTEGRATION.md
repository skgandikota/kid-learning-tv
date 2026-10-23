# Alexa integration status

There is no live Alexa skill, account linking, cloud endpoint, audio streaming, microphone capture, or Alexa service integration in the current implementation. `app/integrations/alexa/` is a placeholder package; `tools/mock_alexa_events.py` prints a sample JSON event for local development only.

Ask Rocky is simulated. It does not record or retain audio. The app instead supports manual parent-assisted answer entry. Do not configure Alexa accounts or expect Alexa hardware to communicate with this project.

Any future integration would require a separate privacy/security review, explicit adult setup, documented consent and retention behavior, and an implementation that is not represented by this placeholder.
