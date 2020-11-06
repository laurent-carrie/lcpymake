========
tutorial
========


step 1
------

step1.py

the steps are :

* the name of the function has to be `main`. This is what the caller expects from you.
* the function has to return the graph. This what the caller expects from you.
* create a build graph, with `api.create`
  the path to the source directory
  give the `srcdir` and the `sandbox`
* add source nodes, with `api.create_source_node`,
  give it the `artefacts` (the files), and a scanner. We will see the scanner later.
* add built nodes, whith `api.create_built_node`, give the `artefacts`, the `sources`,
  and a build rule. We will see the syntax of a build rule later.

.. literalinclude:: ../tutorial/step1.py
    :linenos:
    :language: python
