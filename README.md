A Python framework to encapsulate AWS CloudFormation stacks
===========================================================

This is a hare-brained, off-the-wall experimental project I worked on for
a week or two in early 2012, before giving it up for a Bad Idea.  I thought
I might as well convert it to Git and throw it up here;  maybe I'll look into
it again.  Some day.

The Big Idea
------------

Writing Amazon CloudFormmation recipes directly in JSON is a laborious,
error-prone task that's hard to do programmatically.  It's well-known that
a Python class hierarchy (well, any class hierarchy) maps well to JSON.  And
(instantiated) Python classes are *very* easy to manipulate (also
programmatically).  So why not represent a CloudFormation collection of
resources as a set of Python objects, manipulate them programmatically (or even
interactively), and then serialise these out to JSON if and when?

Why it didn't work
------------------

Multiple reasons.

- CloudFormation recipes are a rater irregular, "evolved" format, and don't
  map as neatly to a logical class strucutre as you might expect.

- To work optimally, the code would have hooks all over the place to do type
  checks.  Whenever you're doing that in a dynamic language, it's a sure sign
  you're using the wrong language for the job.

- Lack of time.  Changing/other interests.

Additional ideas
----------------

It also occurred to me, at the time, that being to "instantiate hardware" from
Python code would make it an interesting prospect to have a Python-based
workflow system (running locally), "creating hardware" on the cloud as and when
needed.

Still not a bad idea in isolation, but the subsequent availability of Amazon
Simple Workflow Service obsoleted it completely.
