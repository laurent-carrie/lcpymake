============
Introduction
============

This is Yet Another Build System. It fits my own needs, I started it because I needed it to write my own songbooks,
with input and generated files as

* rst files, (it uses sphinx)
* json files. index.rst is generated from rst, I want to generate different songbooks (sphinx documents) from the same sources
* lilypond files .ly
* generating png file from lilypond, to have images of the scores
* generate tex for pdf rendering
* .mp3, generated from ly files, using fluidsynth
* extracts ( for instance only the verse or the chorus )
* scan to know who depends on what
* upload to s3 or gcp so my friends for my band can see it
* optimize build time by not running unnecessary commands ( sphinx is fast, but latexpdf or fluisyth are not if you have a certain number of files)

well... it was way too difficult with a regular Makefile. Being an `omake <http://omake.metaprl.org/index.html>`_ lover and having used it successfully
for industrial projects (C++, Json and OCaml) , I gave it at try, but it's hard to customize.

some ideas from omake :
-----------------------

* have a graph of the artefacts to build, their dependencies of the rules
* do not depend on the directory tree, the dependencies are only based on files. See the famous `Recursive Make Considered Harmful <http://www.real-linux.org.uk/recursivemake.pdf>`_
* hash the artefacts. Depend on the digest of the dependencies, not on their date. This will avoid running unnecessary commands
* define scanners. Make provides make depends, but this is difficult
* allow :ref:`variability`

some other ideas :
------------------

* makefile are hard to write. This is why implicit rules are created, but then they are hard to customize. For instance,
if different .o files need different rules to built, that will be hard to code.
* here the build graph is captured with a python script, which is very easy.
* makefile variations are hard to write. ( rule or target that depends on targets )


caveats :
---------

* multithreaded build ( omake -j ) is not implemented (yet?). This would make build much faster.
