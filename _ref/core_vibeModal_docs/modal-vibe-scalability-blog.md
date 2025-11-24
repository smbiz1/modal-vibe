# Modal Vibe: Scaling AI Coding to Millions of Monthly Sessions

**Authors:** Joy Liu (@qjoyliu) - Member of Technical Staff, Charles Frye (@charles_irl) - Developer Advocate

**Original URL:** https://modal.com/blog/modal-vibe
These days it seems like everyone and their mother is vibe coding — running untrusted LLM code in REPL tools, for AI code reviews, in coding agents. If you want to run these workflows without your vibe getting seriously harshed you need a secure, snapshottable runtime environment, like Modal Sandboxes.

This is a real tweet screenshot from a real slide from a real AI conference in 2024. The tweet is now private, because people can’t behave.
Most examples you can find online cover spinning up just one or a handful of runtimes. That’s fine for personal use or for a prototype to impress your CEO, but what if you want to build something for your company or team that manages a fleet of 10,000 applications running in parallel? Does that immediately kill the vibe?

We built Modal Vibe, a simple, scalable vibe coding platform on top of Modal Sandboxes, to demonstrate that impeccable vibes and incredible scale can go hand-in-hand. In just five minutes, Modal Vibe can scale up from 0 to 1000 AI-coded apps. We released the source here. You can try Modal Vibe here.

🚧 Vibe Check 🚧 Like the vibe-coded projects it runs, Modal Vibe is only a demo. If you’re interested in running Modal Sandboxes at scale, don’t just copy-paste the code and YOLO to prod. RTFM and contact us on Slack if you run into trouble.

Architecting for vibes
Agnostic to underlying infrastructure, a vibe coding platform has three main components:

A “sandbox manager” that builds and manages vibe-coded apps.
A web frontend that displays the vibe-coded apps.
A fleet of sandboxes running vibe-coded apps.
#1 and #2 are straightforward to build and run, but introducing #3 adds a lot of constraints to the system.

The common choice is to reach for a workload orchestrator like Kubernetes or Nomad. This is widely acknowledged to be a pain in the ass. Worse, it’s unlikely to meet your startup and scalability requirements.

Fast boots help you scale up and down quickly as heavily vibing users create and discard apps with reckless abandon and the attention span of a goldfish on TikTok. And you need to reach large scales on the order of minutes to handle traffic spikes, like when a LinkedInfluencer sends their audience your way.

We built Modal to solve these problems so that you don’t have to. We can start up a new Sandbox in seconds, produce Sandboxes at a rate of thousands per second, and run tens of thousands of your Sandboxes in parallel. All of this can be done using a few lines of Python code and comes with built in monitoring and dashboards.

We built Modal Vibe on top of Modal as a proof of that concept. The source is available here.

Here’s a video of the user interface and the dashboard during a scale up from zero to over a hundred users. Sound on for this one, it’s got a vibey track from Suno (which runs on Modal btw).

How scalable are we, really?
The video captures the chill vibe of scaling up on Modal, but what about the numbers?

We wrote a simple script that makes REST API requests to Modal Vibe to programmatically create arbitrarily many simple web apps in Sandboxes. We used it to create 1000 separate apps (shouts to Claude, the true 1000x engineer). Each app had its own Sandbox.

We measured the time it took to scale across three orders of magnitude. Note that this includes the time for the AI API to generate the code for the app, which is about 90% of the latency for a single app.

Here’s what we found:

Number of apps (N)	Latency (0 → N, seconds)	Throughput (apps per second)
1	~30s	~1/30
10	~60s	~1/6
100	~150s	~2/3
1000	~300s	~3
Note the increasing throughput with scale. In the end, the AI API becomes the rate-limiting component.

On Modal’s Team Plan, users can run exactly this load test and scale to 1000 concurrently-running Sandboxes. Assuming, based on some anecdata, that the average vibe coder spends about half an hour per session, that’s enough to support a load of 2000 sessions per hour, well in excess of one million users per month.

And that’s just the Team Plan, which you can start using today with nothing more than a credit card. If, like our largest customers, you need further orders of magnitude of scale, then talk to sales about our Enterprise Plan (we promise they have good vibes).

Vibe at scale right now
We released the code on GitHub here, so you can read the details or deploy it yourself. You can also try our deployment here — until the Anthropic API rate limits us.

Teams running millions of sandboxed applications turn to Modal for their infrastructure. Learn how Quora uses Modal Sandboxes for Poe here. We do GPUs and inference too! Learn how Zencastr uses Modal’s GPUs and Volumes to transcribe audio thousands of times faster than real-time here.

