the full doc is written with sphix.
to read it, git clone the package, and run `sphinx-build -M html source build`

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
* provide a clear separation between source and build directory. We will call them `srcdir` and `sandbox`. The mount
  command will copy the source files from `srcdir` to `sandbox`.
* when executing a rule, check that the target that it is supposed to create is actually created. make does not do it,
  which is error prone
* being able to modelize rules that have more than one generated artefact. For instance, a code generator may generate
  a bunch of `.cpp` and `.h` files.
* being able to modelize a dependency towards other artefacts. For instance, if a target is generated with a code genearator,
  the code generator should be generated first
* minimum run : if the digest of a file does not change, do not propagate the build. For instance, if you add a comment
  in a `.cpp` file, this will trigger the compilation of the `.o`, but **not** a new link, because the `.o` will be the
  same as before.


some other ideas :
------------------

* makefile are hard to write. This is why implicit rules are created, but then they are hard to customize. For instance,
  if different .o files need different rules to built, that will be hard to code.
* here the build graph is captured with a python script, which is very easy.
* makefile variations are hard to write. ( rule or target that depends on targets )


what it does not do :
---------------------

* it does **not** provide any support for all of kind of compilers, shared library or dll. This tool just builds the graph,
  you have to write yourself the build rules. So if you write a big C++ program you should use autotools or omake
* multithreaded build ( omake -j ) is not implemented (yet?). This would make build much faster.
