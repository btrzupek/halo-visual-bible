---
title: I illustrated the Gospel of John on a box on my desk
description: 88 scenes over one evening and a morning, all generated locally on an AMD Ryzen AI Halo box and driven from a chat with Claude.
hero: halo_edit_00014_.webp
hero_caption: John 6:19. The fixed version. The first try had a third arm.
---

# I illustrated the Gospel of John on a box on my desk

<p class="byline">Brian Trzupek · September 2026</p>

I got my hands on one of AMD's Ryzen AI Halo boxes and wanted to see what it could actually do. Not a benchmark
first. A real project. So I picked something big enough to be a stress test and personal enough that I'd care how it
came out: a fully illustrated Gospel of John. All 21 chapters, every verse, with a picture for every scene.

It ended up being 88 scenes plus two character portraits, and every image was made on the box sitting on my desk.
No cloud image API, no credits, no upload of anything. I did it in one evening and finished it the next
morning. You can [read the whole book here](/bible).

<p class="cta"><a class="primary" href="/bible">Open the Visual Bible</a><a href="/making-of">See every attempt</a><a href="/under-the-hood">Code and numbers</a></p>

## The box

The Halo is AMD's developer platform for the Ryzen AI Max+ 395. 16 Zen 5 cores, a Radeon 8060S GPU with 40 compute
units, an NPU, and 128 GB of memory. Mine came with ComfyUI, ROCm, vLLM and Lemonade already installed, which
saved me a lot of setup.

For this kind of work the spec that matters most is the memory. The GPU only has 512 MB carved out as
"real" VRAM, but it can map about 94 GB of the system's memory. So a 20 billion parameter image editing model just...
loads. On an integrated GPU. Most desktop graphics cards can't do that.

## How I drove it

I don't want to sit in a node graph for hours. I want to talk to it. So the setup is:

- Claude on my Mac (Desktop and Claude Code)
- a small MCP server I had Claude Code build, so Claude can call tools like `halo_generate_image` and `halo_edit_image`
- an SSH tunnel to the box, because ComfyUI only listens locally over there
- ComfyUI on the Halo doing the actual work

In practice that means I say "give me John the Baptist at the Jordan, pointing at Jesus walking toward him" and a
picture shows up in the chat about 15 seconds later. If something's off, I say "fix his hand" and it does.

Getting the plumbing right took a few rounds. The fun ones:

- The latest version of the MCP Python library renamed the class the server was built on, so the first install just
  broke. Pinned it and moved on.
- My first tunnel was a normal `ssh -L` kept alive by launchd. macOS decided it wasn't important enough to restart
  when it dropped. The fix was to let launchd own the port and start a fresh `ssh -W` for every connection. It's been
  solid since.
- The box only came with one image model. Claude went and found the right model files straight out of ComfyUI's own
  templates on the box, and pulled down about 60 GB of them, checksummed, while I got on with other stuff.

## Keeping the faces straight

Making one pretty picture is easy now. Getting the same guy to show up in 88 of them is the hard part.

What worked was simple. First I had two portraits generated, one of Jesus and one of John the Baptist. Then every
scene with either of them used that portrait as a reference image. FLUX.2 klein can take a reference and put the
same face in a completely new scene, no training required. It costs about twice as long per image (15 seconds
instead of 8), and it's worth it.

<div class="pair">
<img src="/images/full/halo_klein_00006_.webp" alt="Portrait of Jesus used as the reference image">
<img src="/images/full/halo_klein_00007_.webp" alt="Portrait of John the Baptist used as the reference image">
<figcaption>The two reference portraits. Every scene with either of them started from one of these.</figcaption>
</div>

## The stuff AI gets wrong about the first century

This was the funniest part. The models are great at "cinematic ancient Jerusalem at dusk". They are bad at
remembering that nobody in AD 30 had a wristwatch.

Claude checked every image before showing it to me and rerolled or edited anything off. It caught most things.
The running tally of what got fixed:

- wristwatches (about 10 of them)
- electric lights and wall sconces (8)
- trousers under the robes (8)
- glass windows, modern skylines, a utility pole, drainpipes, and three flags
- a tattoo on a disciple's forearm
- extra arms and hands (5), one figure with three legs, and a couple of floating objects
- a spiky glowing halo where there should have been a crown of thorns
- and my favorite: "oil lamp" kept coming back as a glass-chimney kerosene lamp. Three times.

<figure class="pair">
<img src="/images/full/halo_klein_ref_00044_.webp" alt="First attempt: the figure walking on the water has three arms">
<img src="/images/full/halo_edit_00014_.webp" alt="After one edit: two arms">
<figcaption>John 6:19, walking on the water. Left: the first try, with a bonus arm. Right: one edit later, 53 seconds.</figcaption>
</figure>

The edits were done with Qwen-Image-Edit. You just tell it what to change in plain English. "The man walking on the
water must have exactly two arms." "Remove the wristwatches from the two men on the right." It's scary good at
that. It is also very literal. In Peter's denial scene there was a rooster sitting on top of the servant girl's
lamp. I asked it to take the rooster off the lamp. It removed the girl. That one I ended up regenerating from
scratch, and she's back in the book now.

<figure class="pair">
<img src="/images/full/halo_klein_00020_.webp" alt="Before: a rooster perched on the servant girl's lamp">
<img src="/images/full/halo_edit_00049_.webp" alt="After: the girl is gone and the rooster moved to a wall">
<figcaption>John 18. I asked it to remove the rooster. It removed the girl and kept the rooster.</figcaption>
</figure>

Claude's checks caught most of it, but not everything. A couple I caught just by looking at the pages. In the
arrest in the garden, one of the soldiers knocked to the ground wasn't really a person. Some armor, a face, and
then... something else. And in the scourging, Jesus had three legs. On a phone you'd scroll right past both. On a
big screen they jump out at you. Each one took a single edit to fix, under a minute apiece.

<figure class="pair">
<img src="/images/full/halo_klein_ref_00088_.webp" alt="Before: one of the fallen soldiers on the right is not quite human">
<img src="/images/full/halo_edit_00039_.webp" alt="After: two normal fallen Roman soldiers">
<figcaption>John 18:6, "they went backward, and fell to the ground." Left: the soldier on the right is not a person. Right: fixed.</figcaption>
</figure>

Chapters 19 and 20 were the hardest. Anatomy under strain is where these models fall apart, and the crucifixion
scenes needed the most passes. Thomas and the wounds took four edits and a fresh start, because the edit model kept
moving the nail wound onto Thomas's hand instead of Jesus's. Lesson learned: if an edit fights you twice, regenerate
with a composition that avoids the problem.

## The numbers

I had Claude go back through ComfyUI's own job history and then run a proper benchmark with power sampling, because
I wanted real numbers.

| | |
|---|---|
| Images in the book | 88 scenes + 2 portraits |
| Total attempts | 168 (103 reference shots, 18 plain, 47 edits) |
| Attempts per published image | 1.87 |
| GPU time for the whole book | 68 minutes |
| One scene (klein, 1344x768, 4 steps) | 8.6 s, or 15.7 s with a reference face |
| One edit (Qwen-Image-Edit) | 32 s warm, 54 s right after switching models |
| Power | 31 W idle, about 156 W flat out |
| Energy per scene | about 0.3 to 0.6 Wh |
| Electricity for the entire book | about 0.18 kWh. Call it 3 cents. |

A few things jumped out at me:

**The GPU was busy less than half the time.** 68 minutes of GPU work over about two and a half hours of actual
session. The rest was writing prompts, looking at pictures, and me deciding what I actually wanted.

**Switching models is the real tax.** Every time I went from generating to editing and back, ComfyUI had to load the
other model. Each one got loaded 27 times. A warm edit is 32 seconds. An edit right after a generate is 54.

**It runs hot and it doesn't care.** Back to back edits pushed the GPU to 100 °C and the package sat at about
156 W. The clock speed dropped less than 1%. It hits its power limit and just sits there.

**The cloud would've been cheap too.** The same 240 or so calls on hosted image APIs would run somewhere between $7
and $32 depending on the model. So for me the win wasn't the money. I could reroll as much as I wanted
without watching a meter, nothing left my house, and I kept every full resolution file.

## Part two: the Gospel of Mark

The next evening I did the Gospel of Mark the same way. 16 chapters, 678 verses, 75 scenes. Mark is shorter than
John and it moves fast, so the scenes do too. You can [read it here](/mark).

<p class="cta"><a class="primary" href="/mark">Open Mark</a><a href="/making-of">See every attempt</a></p>

A few things were different this time.

**Same Jesus, two new faces.** I reused the Jesus and John the Baptist portraits from John, so it's the same Jesus
in both books. Mark leans hard on Peter, and it ends with Mary Magdalene at the cross, at the tomb and in the
garden. So I had Claude make one portrait of each and use them as the reference in the scenes where they're the
main figure.

<div class="pair">
<img src="/images/full/halo_klein_00026_.webp" alt="Portrait of Simon Peter used as a reference image">
<img src="/images/full/halo_edit_00051_.webp" alt="Portrait of Mary Magdalene used as a reference image">
<figcaption>The two new portraits for Mark: Peter and Mary Magdalene.</figcaption>
</div>

**The text got checked first.** Claude pulled the King James text from two separate public domain datasets and
compared them verse by verse before anything got drawn. All 678 verses matched word for word.

**I mostly let it run.** I approved the scene list up front, and then Claude generated, checked, fixed, and sent me
a contact sheet every few chapters.

### What went wrong this time

The checking was a lot stricter on Mark. Instead of looking at the whole picture, Claude zoomed into every image a
piece at a time. That caught a lot more. Only 10 of the 75 scenes were keepers on the very first try. On John it was
closer to half.

The new ones I hadn't seen before:

- **A subtitle.** Claude put a line of dialogue in a prompt ("whose is this image?") and the model burned it into
  the bottom of the picture like a movie caption. Misspelled. Lesson: never put spoken lines in a prompt.
- **Modern cities in the distance.** Any prompt with a town in the background got a modern one. The triumphal
  entry came back with today's Jerusalem skyline, gold Dome of the Rock and apartment blocks included. Gethsemane
  got electric city lights across the valley. The fix every time was to frame the shot so there's no distance to
  fill.
- **Counting.** Ask for seven baskets, get four. Ask for three crosses, get two. For the baskets Claude just renamed
  the scene instead of fighting it.
- **Sunglasses.** One prompt asked for phylacteries on a Pharisee's forehead. The model gave him sunglasses.
- And the usual suspects: lots of trousers, eyeglasses in a crowd, a briefcase, a light switch, an asphalt road with
  a painted center line, and a man lying on a mat with a head at each end.

<figure class="pair">
<img src="/images/full/halo_klein_ref_00215_.webp" alt="Before: a garbled subtitle burned into the bottom of the image">
<img src="/images/full/halo_edit_00070_.webp" alt="After: the subtitle removed">
<figcaption>Mark 12:13-17. Left: the prompt had a line of dialogue in it, so the model added a subtitle. Right: one edit later.</figcaption>
</figure>

<figure class="pair">
<img src="/images/full/halo_klein_ref_00205_.webp" alt="Before: the triumphal entry with the modern Jerusalem skyline behind">
<img src="/images/full/halo_klein_ref_00206_.webp" alt="After: the same scene on a country road with no city in view">
<figcaption>Mark 11:1-11. Left: the Dome of the Rock and apartment blocks. Right: take the city out of the shot.</figcaption>
</figure>

The edit model is still very literal. Asked to swap a fedora for a head cloth on one man far in the background, it
put the head cloth on a Pharisee in the front and made the fedora sharper. Six of the 28 edits on Mark made things
worse and got thrown out.

One new annoyance on the plumbing side: every single edit timed out on the Mac end, even though it finished fine
on the box. Claude worked around it by pulling the finished image straight from ComfyUI. That's the next thing to
fix in the MCP server.

### Mark by the numbers

| | John | Mark |
|---|---|---|
| Scenes | 88 | 75 |
| New portraits | 2 | 2 |
| Total attempts | 168 | 188 (160 generations, 28 edits) |
| Attempts per published image | 1.87 | 2.44 |
| GPU time | 68 minutes | 98 minutes |
| Session length | about 2.5 hours | about 2.9 hours |

Mark took more attempts per picture than John even though it's the shorter book. Most of that is the stricter
checking. The box was also slower across the board this time. A typical scene took 22 seconds instead of 16, and
a typical edit took 92 seconds instead of 53. I don't know why yet. That's on the list too.

## Try it

Everything is on [GitHub](https://github.com/btrzupek/halo-visual-bible): the MCP server, the ComfyUI workflows, the tunnel setup, the book viewer,
and the scripts that pulled these numbers. The [under the hood](/under-the-hood) page has the full hardware and
benchmark breakdown, and [making of](/making-of) has every single attempt with the exact prompt, including all
the wristwatches.

Next up will be integrating this into my agentic coding workflows.

IF you made it this far! You are amazing. Thanks for the read. I will keep you posted on my next test and workflow. This box is incredible, thank you @AMD!
