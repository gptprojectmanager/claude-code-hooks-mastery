The Complete Claude Code Workflow (90% Skip This) [AXz6TMAwqnY].en.vtt
====================
Cloud Code has become my go-to coding
agent for the past few months. In this
video, I'll show you all of the
workflows and features that I found
incredibly effective over the past 3
months of intense usage. I'll also show
you the custom tools I built to make
those workflow even more effective.
Quick update before we dive in. I'm
super excited to be launching Beyond the
Hype newsletter, where you can receive
all these pro tips and insights directly
in your inbox, plus insider only content
and early access to my future projects.
Subscribe at beyondthe.dev.
Now, back to the video. The first part
of the workflow, use tests wherever you
can because when you write tests in your
codebase and give cloud the capability
to run those tests, you give it a
mechanism to automatically feed back to
itself on its own runs. So when it
implements new features, claude can just
directly run those tests to verify
everything is working before returning
to you. Otherwise, the workflow most of
us would go into in the prototyping
phase is getting called to return. you
go to manually test, copy and paste the
errors back into cloud. Cloud goes into
debugging mode and rinse repeat. That
can waste quite a lot of time and it's a
lot of interrupt for the human working
with code. But when you have test, all
of these workflows are automated. And
this works especially well for larger
complex code bases or even for smaller
code bases but working on complex
features. I know at this point many of
you might be thinking well I'm just
writing my prototype I don't want to
spend so much time writing test can I
skip this yes you can actually because
for claude just adding a phrase whether
in your claud md file or just in your
prompt to say you know testing this
feature before returning claude will try
to at least either write test itself ad
hoc on the run or it will try to write
temporary scripts to test the API or the
UI as the implement itself. But just by
having that one line in will make Claude
try to iterate harder on the work is
outputed yourself. One thing I found, if
you don't give it any additional prompt,
Claude will only really try to test its
own code about five out of 10 times. So
just enforcing this behavior will give
you really great results. If you haven't
already, look at how you can add test
frameworks for your current setup. And
trust me, you will not regret any minute
you spend in it. Testing by itself
probably already deserves its own video.
Let me know in the comment below if you
want me to dive into this in further
detail. The second part of the workflow
being really mindful about Claude codes
memory. So this is essentially the
claude code rules files that you can
apply that claude follows upon every
single run to make sure it has the right
context about project so that it knows
you're coding standard. It knows your
workflows. Claude actually gives us a
super convenient way to initialize this
claw.md file that sits at the root of
the repository. So you can run the init
command inside your directory and you'll
see it reading through all of the
project context, the other agent rules
files. Well, it knows how to learn from
cursor and GitHub copilot. Um, read
through the file directory and the
readme, a lot of the key text files,
then analyzes all of that to generate
this overarching claw.md file. Well, one
thing that you'll see inside the cloud
MD file is the project's overview about
what the project does, key workflows and
architecture, text stack, folder
structure, and a lot of the highlevel
information about the project, even some
highlevel critical library information
in there as well. As you iterate through
the project, there are will be points
where you need to update this context.
So you can just run /init command again
to get those things updated without
having to do this manually. One thing to
keep in mind for working with the
claw.md file is you want to make sure
that you don't overload it with every
single fine detail in your project
because cloud code is actually pretty
decent at discovering information on the
run. Much like how it's doing the nit
commandcl.md file generation in the
first place. It knows how to explore the
codebase to find the information it
needs. Claude.md file is really the
highlevel pointers that you give claude
so that it knows where to find the right
information. You can already see that
inside my current init run because I
already had a claude MD file directly
inside the repository. It's discovered
some updates I've made to the project
and also now suggesting updates. And
I'll just click on shift tab to auto
accept these edits for now. The other
principle to keep in mind when working
with claw.md file is to make sure that
you only add things into this file when
these are the rules that should really
be followed with every single one of
your claude prompt runs. Most of the
times because claude code is already
great actually writing decent code and
following the best practices. If you see
claude already doing the right thing
most of the time then there's no point
enforcing it additionally with
additional rules. Claude also gives us a
credibly easy way to add new memory. So
we can just do hash anywhere inside the
input box and during the prompt and we
can say that and let's just use the
example right always use descriptive
v names and we'll choose to save it into
the project memory. So the ones that we
have committed and it will add this in
in the background. And now if we open up
the cloud MD file, you'll see that it's
added this new rule directly into the
memory file and even added a new heading
specifically for that. So that's a great
thing about this hash command. It will
know to take the new memory rule that
you want to add in and insert it into
the right place inside the memory. And
at times if this is actually relevant
and applies to multiple rules within
your cloud MD file, it will insert that
into multiple locations and it will take
the semantic meaning correctly making it
super easy for you to add these things
ad hoc. There will be times when you
want to give very specific commands to
claude where you have a lot of
additional context for a specific subset
of task. You can use the commands
capability inside of claude code. You
can add this into the commands folder in
the cloud repository. Let's create a
directory and add a code review command
specifically here. So in this file, you
also have two directives that you can
use. You can use the dollar arguments
to allow arguments to be passed in
directly into this command when you
execute it in cloud code. You can also
use the exclamation mark and then
quoting it with the bash commands that
you want to run to include the output of
those bash command directly into this
thing. So here let's write the file
instead of claude. Let's restart it and
you'll see that we have now the /code
view command directly here and we can
click on that and it will go into the
review mode to execute the current
working set. This is incredibly
convenient if you will have a specific
set of workflows that you want to
hardcode that requires additional
context but without having to pollute
the rootcl file. Next key part of the
workflow context management. Even though
all of the latest cla models have
200,000 context windows, one thing I'm
sure you've noticed is that as your
conversation length with a claude grows,
its response just degrades over time.
You'll want to be really mindful of
what's currently in the cloud codes
context while you're executing.
And if we go back to the workflow that
we had already started, whenever you
finish a task, the first thing you want
to do is clear the existing context
because most of the time given how great
Claude is at discovering information
from the repository and the fact that
you've already got much of the overview
directly in your cloud. MD file, then
you can easily start from fresh. I'd say
slashclear would already be sufficient
for 90% of the use cases. But maybe
you've just had a long conversation
during a debugging session and you want
to carry some of the information that
you found and the decision you found
directly into your next feature
implementation. You also have the
compact command which cla also runs
automatically whenever its context
window is fully filled up or you can
manually trigger it before you go into
the next piece of work to give you a
cleaner context. And the cool thing is
as you can see in the instruction you
can provide additional instructions for
it to focus on during this
summarization. So Claude will take out
all of the key decision made and code
changes and put that into a much more
compact format without retaining the
entire message history and then start a
new conversation based on just the
summary. This is great when you're
working on a new workflow, but what if
during your current flow there's things
that has gone wrong and you need to
revert back to a previous point of the
conversation? Perhaps you've noticed
you've misled Claude down a wrong path.
You can press the double escape key at
any point during your command execution
and then select a message to actually go
back into. Let's say we go back to the
place before it did the code review here
and we get here, right? So, this is
really convenient for you to just clean
up the context on the go. You can see
claude actually gives us quite a few
tools in our pocket to control context.
I think the claw devs really know that
this is something that's really key. But
there is one caveat though. Unlike
windsurf and cursor, when you navigate
back in the message history, it doesn't
actually revert your codebase back to
the point at that message. So you have
to do version control yourself manually.
I really hope that the claw team adds
this in sometime soon. The next part of
the workflow, permission management
during tool executions. So by default
you'll see that when you start up a clot
code command it will start in the
default mode which is pretty much read
only. So this thing is actually great
for doing codebase explorations and we
just need to find out things within the
codebase because if not the default
workflow that you should really go to is
the autoaccept edits mode which you can
cycle through these modes by shift tab.
It also has the plan mode which forces a
plan then act workflow so that it
basically starts clot code in a readonly
mode generates the entire plan for you
to review and I waits for your approval
for the plan before it goes into the
autoedits execution mode. And if we exit
the command here there's also another
very well hidden command called
dangerously skip permissions. This can
only be enabled when you start up claude
at the command line. And you'll see that
on the bottom right hand corner, it will
say bypassing in permissions. In this
workflow, Claude will run all commands
whatever the batch commands there and
without any confirmation from the user.
This workflow is great if you're working
in CI or if you have got a great dev
container setup. But if you're using
this on your main dev machine, I'd
recommend not to in most of the cases
just in case something goes wrong. One
thing I would also suggest you do is
changing the default mode that claude
starts up on because the one I almost
always use it is the autoaccept edits
mode. So you can go to claude and then
go into the local settings here. Inside
the permissions block, we can add in the
default mode and we can say accept edits
here. Once we save, let's actually
restart. You'll see that it will always
have the auto accept edits on, which is
super convenient.
With the accept edits mode, it approves
most of just the plain file edits. But
when it comes to running any bash
commands, even lss directly inside your
repository, it will ask for your
approval, which can be quite annoying.
I've had a lot of times where I've
started cloud code on a task which I
thought it would be able to complete by
itself only to return terminus later
realizing that it got stuck on one
command approval at the very beginning
of the execution run which is fairly
annoying because I want something
between the dangerously permissions
and the autoaccept edits mode. I've
actually created a new tool called cloud
code boost that uses LLMs and actually
uses the cloud models to look at the
command at every single tool call decide
whether should auto approve it given
that it's standard development workflow
and then injecting that directly as a
hook inside of the repo does all of the
auto approval but without the worry that
it would execute some dangerous command
without asking for your additional
approval. Next part of the workflow,
version control. As I always say, when
you're working with coding agents, it's
great to use version control to always
keep your current repository in a
working state. As previously mentioned
though, Claude doesn't have a built-in
way to do checkpointing. So, you have to
do a lot of this work manually. And the
workflow I generally go into is after
every round of prompting with cloud code
after I see it it's got a working
solution I add the current file into the
gate staging which you can do with a get
add dot and if you want to be more
selective you can choose the individual
files that you want to add specifically
then once you get to a working state
cloud code actually gives us a
incredibly easy way for making the final
commit. So here we can literally just
say commit and it will look through all
of the changes is currently implemented
and if you already had a conversation
history directly with claude it will
also use that as context to only commit
the things it's worked on and ignore the
rest of the changes. It will also look
at the git history to see how commit
messages has been formatted in the past
and then look at the current changes
then create the commit directly. And
because I've already got my tool to auto
approve a lot of the git commands which
is why you didn't see it prompting me
for the confirmation during the git
commit. And here it correctly summarized
everything with all of the feature
additions. And every single time it does
always inject in a generator with cloud
code, which I'm fine with given the
great work it's actually done. I would
highly recommend adding a pre-commit
checks directly into your repo to give
Claude even more automated feedback. I
use a tool called Husky to add in these
kind of pre-commit checks. The three
things I always have in there, the
compile checks, the lints, and quick
unit tests. So every time claude goes to
commit the work, those pre-commit checks
will run automatically and claude will
be able to directly act on the errors
and then correct fix all of the issues
before it commits the code. So these
kind of hard-coded workflows really
enforces the high quality of code Claude
commits every single time. something
really simple to add in, but just make
sure that you never go into a broken
repo because every single one of your
pre-commit checks ensures that the repo
is in a working state. The last part of
the workflow, async work together with
claude. Claude code provides a very
convenient way to install the GitHub
plug-in directly here, which is what
we'll use for this async workflow. And
during this process, it will confirm
with your repo, install the plug-in and
add in the all tokens and also add in
the GitHub workflow files to
automatically execute claude code and
also code reviews as part of all
changes. You can see that we've got two
new workflows here and one which is a
review that will trigger every single
time a pull request is opened. The thing
I would really suggest is inside the
prompt here, customize this based on
your need for code review because the
default code view provided by cloud code
can be quite verbose and generally I
only have identify potential bugs and
also security concerns. Then ignore all
else. And the next one is the claude or
yaml which allows you to atmention
claude in any GitHub comments whether in
issues or inside reviews. Clawed code
will then take the comments as context,
then directly make the changes and then
update the branch accordingly without
having to set up any local environments.
This workflow is especially powerful if
you've also got automated test setup
because then you can have Claude
iterating on new features, working on
new things directly in the cloud and
only returning to you in the code review
with updated and relevant code so that
you can directly just review the code
and merge when everything actually
checks out. This is just an example of a
cloud code reviewed pull request. You
can see that the review is extremely
comprehensive with a lot of actionable
comments directly in there. And
obviously, this is before I'd optimize
it. Just focus specifically on security
issues and bugs. But you can see how
powerful the workflow can be. And here
is another usage where inside my GitHub
issues, I've asked it to make a specific
change inside of my repo. When I
mentioned add cloud here, it will go
into the execution mode and show you all
of the to-do updates much like it does
for you on the CLI and then shows you
all of the work it does, the key changes
made, and the next steps for you to
actually follow up on. Once the work is
complete, it will give you a link to
directly create the pull request, which
is incredibly convenient. Hopefully here
I've given you another reason to write
great tests inside of a repo to give you
a even more powerful workflows like
this. Now that we've done with the
workflows, here's a quickfire list of
very useful utility features I found
over the past 3 months of usage. As
previously mentioned, you can use hash
to directly add memories conveniently.
You can use also the exclamation mark
for running bash commands for claw to
directly add in the output of the
commands into its context. And also
during the clot thinking process you can
use keywords like think or think hard
think harder
also ultra think to trigger different
levels of thinking budgets for clause
models. And I would say use this
sparingly because it uses up your
quotota really quickly and I've rarely
had to use these things to solve
problems directly in my codebase.
Anywhere you've noticed clause falling
down a trap and it's just not able to
come up with the right solution, try
these keywords in turn inside your
prompt to get it to think harder and
harder to try to resolve the problem.
And if on the max plan, sure, you can
always apply the ultra think every
single time to get it to solve the
hardest problem. But the general
recommendation is to go through these
step by step. As we have also typed
here, because it's a command line tool,
you would think that it doesn't have a
lot of the convenience features to undo.
They recently just added a shortcut for
control plus dash to allow you to undo
types directly inside your terminal. And
this is incredibly useful if after a
long command that you realize you've
accidentally just deleted the whole
line, then you can easily bring your
content back with control plus minus.
Many people say that claw didn't have a
easy way to deal with images. In fact,
it did actually from day one. Let's take
a screenshot of claude code itself and
then we can press Ctrl +V to paste the
image in. You can ask it what is this?
And you'll see that Claude is able to
use its vision capability to analyze the
image. It works amazingly great if
you're working with UI. So you can just
pasting errors without having to deal
with the copy and pasting so that Claude
can even reason about element positions
and things like that during its
debugging process. Additionally, if
you're working with larger repos where
you have a multi-reo setup or maybe
you're just working with an open source
repo where you need reference to, you
can also use the command for add
to specify additional directories that
your current cloud code instance should
also have access to. Once you do this,
it will be able to read through it and
also make changes directly when you do
this.
And now if we just exit claude a bit,
there's a few cool things also on the
outside. We'll create something new is
there's the non-interactive mode for
claude. You can use this to get claude
to execute on the command but not print
out any of the thinking process and only
give you the final output. And the
simple one, you know, like cla what is
the date? It will run obviously a bit
slower than the traditional command.
then only output the final result.
Command is also incredibly useful if you
just want to run something quick but
don't really care about the thinking
process. You can say what does this
project do? We can wait for Claude to
actually generate this response and you
can see that it goes through the summary
and just get the output here.
There will be times where you might want
to return to a point inside your cloud
conversations. So here you can use
claude d-res
to go back to a specific conversation
that you've had. I think I really hope
that they create a better summary rather
than just using the first message. But
it's okay. And then now oh actually it's
added the branch it was on while it was
working on this feature. So making it
quite easy for you to go back in history
to find out what's going on there.
And if you are just continuing with the
last conversation, you can use cloth d-
continue to run those command very
easily. And now we're going back to the
one that we just run non-interactively.
And you can see the conversation it did.
If you ever need to debug the
non-interactive mode, well, this is how
you do it. Well, there you have it.
There's a ton more things that you
should go back to try with your cloud
code workflow. As mentioned earlier in
the video, if you want these insights
and pro tips directly in your inbox, be
sure to subscribe to beyond the hype.dev
newsletter. And until then, happy
shipping and I'll see you in the next
one.