I Reverse-Engineered Claude Code： Learn These Agent Tricks [i0P56Pm1Q3U].en.vtt
====================
I've always wondered why does claude
code feel so much better than other
coding agents despite having the same
models under the hood. In this video,
I'll show you my journey reverse
engineering cloud code to find its
secret sauce. Show you how you can
leverage this understanding to extract
way more out of it and take away
principles for building your own coding
agents in the future. Quick preview.
It's a lot of prompt engineering. Quick
update before we dive in. I'm super
excited to be launching Beyond the Hype
newsletter, where you can receive all
these pro tips and insights directly in
your inbox, plus insider only content
and early access to my future projects.
Subscribe at beyondthe.dev.
Now, back to the video. When Clot Code
was first released, I got quite excited
thinking it was going to be an open
source project, but it wasn't. All we
have is this bundled 9 megabyte CLI.js
file for us to analyze. So we'll dive
straight into that. I use a tool called
WebCrack here to unbundle and
deoffiscate the compile.js file. And
what I got at the end was quite
shocking. It was a 443,000line
long JS file for us to analyze. And
looking into the file, there are ton of
cloud codes dependencies built in. But
what I really want to find is the
prompt, the LLM interaction claude code
actually makes. So I started searching
for the text cloud code directly in the
file. Found a couple usage and quickly
realized that much of the prompt and LM
APIs are very much dynamically
constructed. So there wasn't a long
string piece of text that we can easily
directly extract out of this. So I had
to change approach very quickly. And
then I realized that clot code allows
people to manually set the anthropic
base URL environment variable which must
mean that cloud code is actually making
the LLM request directly with the
original content. Otherwise this base
URL wouldn't work. So if we throw a
proxy in there to intercept the request,
we should be able to capture everything.
Then moving on to approach two, I used a
tool called proxy man to intercept all
of the requests between cloud code and
the anthropic APIs. And voila,
everything started appearing. You can
see for every cloud code interaction,
there are ton of messages that get sent
to the anthropic API as expected. And
just to walk you through the core parts
of a anthropic API call, you have the
user message which contains a full
message history, the system prompts and
the tool definitions, but also the
response as well as the occasional tool
use. Let's actually go into a diagram to
illustrate this more cleanly. So the
client is our cloud code, LM API,
anthropic, and the tools that we've
defined. At the top of the message
history, you always have the system
prompt that defines the agent's role.
And then we'll have the tool definitions
that's also included just below the
system prompt. Then the user message
actually comes in with a request. Let's
say we're checking out the weather here.
We call out to the anthropic API with
this request. Then the assistant will
respond with a message and likely some
further tool calls to execute to get
more information. Our client then takes
those tool calls based on the
definitions, calls out to the relevant
APIs and tools, get the results, appends
that to the history, makes another
request to the LLM API. Then we see it
responding with more request and then we
do a few more rounds of this tool calls
getting the results responding to LLM
and at one point the LLM will decide
that okay the work is done and return
the final message to the user and say
here it decided to get the weather
condition in one round get the
precipitation and then finally return
the weather summary directly to the
client. So that would be the final
summary message that you see inside of
clot code. That's the core orchestration
that cloud code does locally. Albeit it
has a ton of other UX improvements which
we won't cover in this video. But the
true meat lies within the system prompt
itself. Here is the system prompt that
I've extracted from the intercepted
request and clearly formatted. The
system prompt here covers everything
from responding to user documentation
request, tone and style, how we should
be proactive and how to follow
conventions. The only coding style never
add any comments. Funny that even with
this in the system prompt, we still see
a ton of comment that Claude tend to
add. How it should be doing task
management, how it should be working on
using tools, and finally how it should
be referencing code. Quite a long file.
I won't walk through every line, but
we'll focus on the key observations.
Number one is that the core workflows
has to be reiterated quite a few times
across different sections inside the
same system prompt. Take the to-do tool
as example. That's a tool that claes to
show you the lovely checklist as it
progresses through the task. And we see
that mentioned in multiple sections of
this document inside the task management
and even shown with examples of how it
should be managing the different type of
task. One with breakdown, one without
breakdown. And then during the executing
tasks, then using the to-do write tools
as required. Then finally in the tool
use policy with another reminder that
always use the to-do files to plan and
track tasks throughout the conversation.
And you also notice that these kind of
modify use across the document. Things
like important, very important, never,
must. You use this to iterate on things
that the LLM should pay special
attention to. You'll notice that these
descriptions aren't exactly short. So,
these reiterated long detailed
descriptions and clearly stated with a
ton of examples spread around this whole
system prompt is how cloud code is able
to get those extremely accurate function
calling capabilities out of it. If we
compare the mention of to-do write tool
to the lint tool here, lint does
actually get mentioned. Claude even
specifies that when you have completed
task, you must run lint and type check
commands. In my experience, claude code
maybe only does that five out of 10
times. So not reliable at all. And this
is clearly reflected in the fact that
lint is only mentioned once compared to
the to-do write which is mentioned in
multiple places so that you get
different reliabilities for these
different commands. I always also add
the requirements to run lint and type
checks directly in the cloud.md file to
have a better experience. Cloud code
actually has another way of further
reminding the model of key tool call
requirements inside our message history.
It also adds this system reminder block
for the model and reminding it that
there is a to-do list and the to-do
write tool to use it should it benefit.
This gets reinserted after every time
the task progresses and after every call
to the to-do write tool. This is by no
coincidence that clause to-do management
and planning work so well is precisely
because of this constant reminder of
these key tools inside the message
history. So next time when you have to
remind cloud code of something, don't
feel too bad about it. It's not you,
it's just that agents forget. The second
observation here, all of the workflows
inside of cloud code is pretty much
defined inside the system prompt. Say
for task management, you can see that it
clearly states the style it should
manage its task on and even gives
examples of how it should be working on
the task breakdowns. A simple task that
didn't need it and a more complex ones
that did require it. And inside the
doing task, it clearly outlines how it
should be using the to-do tools to
further track and how to use the search
tool and also well the lint check it was
being reminded of and never to commit.
So much of this is all defined directly
in the system prompt in natural language
and not hardcoded inside of the CLI.
This is actually quite powerful because
if you need to change or vary any of the
behavior, you just need to change the
prompt. There's barely any code that you
need to change. Maybe there's UX
improvement that's required to deal with
the user approvals, but to change the
core flow is all very much just about
the prompt. The third observation here
is that formatting is still quite
important. This system prompt one is
very much human readable and two having
the structure actually adds more
semantic meaning to the text. For
example, inside the coding section we'll
see that everything is all caps
important. Do not add any strong and
bold letters comments unless asked. So
all of this formatting is actually taken
in by the model when they try to
comprehend this prompt. Additionally,
the use of XML tags is also really
powerful here. As shown in the previous
example sections, you can use these XML
tag pairs to clearly outline sections of
text that the LLM should respect as a
single cohesive piece. You can also nest
these XML tags much like how you would
write any XML documents to add more
semantic meaning. So if you have
something that's a bit more complicated
that spans multiple lines, using XML
tags to format will yield some great
results. Now that we understand how the
main agent work, let's dive into a more
interesting feature, sub aents. This is
a feature that Cloud Code recently
released to allow the main agent to
trigger sub agent to run specific sets
of tasks with their own defined system
prompts. Here's how it works from a high
level. You'll remember that we have the
system prompt at top and the tool
definitions the user input and based on
the first LLM call we get a response
back and together with some tool calls
and the agent here is actually just
treated as another tool that gets
triggered. Let's say that one of the
tool call here actually called out to a
subject agent to be created. Then cloud
code will create a new message history
for this sub aent. The sub agent gets
its own system prompt and then the tool
call will contain the message it should
start with. This user input is provided
by our main agent. Then this continues
to execute much like our previous
history. Right? You'll have the
assistant messages and then that
continue with the tool calls. Then you
get some tool called results. Here this
cycle continues until at the end the sub
agent decided well from the LLM calls
that the work has been complete and so
it returns a assistant message without
any further tool calls returns to the
main agent and this final message gets
appended back into the main agent but
not as a system message here but as a
tool call result. So this gets appended
back. So much like the main agent will
call out to say a read tool to get the
content of a file, the edit tool to
change the content, equally when it
calls out to the agent, it delegates a
task and then gets just a summary back.
Notice that all of the message history
in the middle is actually discarded
here. This is actually very very
important because when you delegate
tasks to sub agents the memories between
the main agent and the sub agent is
actually not shared. So you want to make
sure that whatever message that gets
returned to the main agent that's all
the information the main agent is
actually going to need to execute on
that task to avoid rework. Then the rest
of the agent will just continue like
normal. Just to give you an idea what
this looks like in the actual request
here we have a user message that asks
the main agent to use a require analyzer
agent to plan the work. You can see that
in the response here it creates a tool
call and starts up the requirement
analyzer agent with a very detailed
prompt on the creation. Obviously this
input for the sub aent call is
synthesized from the claude or MD
context together with the user input. If
we go on to the next message, we'll see
that it again gets the same cloud. MD
file and only the input the main agent's
memory is also not shared here. And our
agent will then to continue doing the
work. It starts with a whole bunch of
file reading before it continues. Our
sub agent then executed for a few more
rounds of the request. In the final one,
you can see the message history here on
the left with the tool calls and the
tool call results. Then it returns with
the final message of the summary for the
requirements. This summary gets taken
back into the main agents memory message
history. Then just gets shoved in as the
result for the tool call. So the tool
call that we previously saw here. And
then the results gets inserted directly.
Note that the middle of the message
history for the sub aent run is
completely dis discarded. And then the
main agent continues running like
normal. And because it was reminded of
the to-do tool here, it used the to-do
tool to create the plan. Then continues
executing for the whole task. This goes
on for another 30 40 requests before the
agent find the Rutanza user with the
final implemented feature. At this
point, you're probably thinking at no
point in the system prompt did it
mention the requirement or the need to
use sub aents to work on task. So, how
did Claude end up knowing to use that
thing? The secret is all defined in the
tool section. So if we scroll past the
system prompt here, we'll see tools
actually defined. The task tool is
basically the thing that manages the
launch for new agents to handle complex
and multi-step tasks autonomously.
You'll see that this description is
again very much detailed compared to the
traditional MCP tool oneline description
that we're used to seeing. Let's
actually break this down further. Here's
a description. nicely formatted. You'll
first see that it lists all of the
agents that's available to call and
again abundant amount of examples of how
we should be triggering those different
agents. The tool that's available to
each one of the agents as well as the
when to use and when not to use the
agent with a ton of examples including
notes on how it should be extracting
information directly from the agent.
Much like the system prompt, there's a
lot of detail in here. When we see that
cloud code is able to make such accurate
tool calls, these detailed prompts and
descriptions are the key to those
accuracy. We also observe the similar
kind of workflow design that we saw
inside of the system prompt. Inside the
usage note, it will say how we should
launch the agent, how we should handle
the agent returns and how each
invocation is completely stateless so
that there's no additional messages that
get sent to the agent and that's how it
should be trusting the agent, how it
should also be triggering the agent
should it be defined to be used
proactively. So if you've tried to
create sub aents yourself inside of
cloud, you'll notice that during the
creation process, it will ask you
whether you want manual configuration or
generate with claude. The reason that
the generator with claude is marked as
recommended is because Claude actively
adds those detailed descriptions for
your agent together with examples
generated based on your past
conversation history to give you the
best results possible for when executing
those agents. You should additionally
note that when triggering sub agents,
the system prompt for cloud code
actually gets replaced with the agent
description. So for your sub agents to
have similar kind of performance as the
main agent, it needs to follow the exact
same best practices the main agent
system prompt follows to get the best
results. And that's exactly why Claude
generally prefers you to generate those
agent descriptions directly using Claude
because of the extra information it adds
in and also the best practices it will
follow. But obviously once it generates
agent with sufficient detail, you are
more than welcome to go and modify it,
but it would be great to just make sure
you follow the structure there. A few
other notable facts from this
investigation. You'll remember this
/init command call defines that
workflow. Again, not hardcoded, just
another prompt template running here. If
you've ever wondered why it always knows
to look inside the cursor rules file and
also the GitHub copilot instructions
file, it's defined very clearly inside
this prompt. And then the file structure
is also clearly outlined here. And then
also you'll remember the compact
command, the thing that it runs when it
runs out of context. This clearly
outlines the work it needs to do. Again,
a very much detailed prompt with very
detailed descriptions on the workflows,
the dos and don'ts, examples, ton of
great formatting here. Now you see that
there's so much prompting that goes into
this thing. It's also worth noting that
prompt tuning is very much model family
specific. For those of you who have
tried switching out the sonnet models to
use other external provider models,
you'll realize that the tool calling
capability and accuracy doesn't seem as
good as sonnet. And most of the time
this is not due to the fact that those
models are less capable but due to that
these system prompts and I mean all of
the prompt that you see here must be
tuned very specifically to the model
family that you're using. The one that
works for OpenAI might not work anywhere
near as well as it does for set. So
whenever you are switching out models or
even inside your agent build, you want
to make sure that you have evals and
prompt tuning techniques in place so
that you can iterate on those things
really fast. With all that, you can
clearly see great agent loops are
defined by sophisticated prompts with
clear instructions and workflows. Prompt
engineering is still very much a thing
in 2025 and it will continue to be for
quite some time. You're now armed with
all of the principles needed to start
building your own coding agents. If you
want to learn more about how to leverage
cloud code to extract more value out of
it, check out this workflow video just
up there. Until then, happy shipping and
I'll see you in the next one.