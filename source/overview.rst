========
overview
========

This is a python module, once installed it provides :
* a python module, that you use to build your graph
* a runtime program

Assuming you wrote your graph in *mygraph.py*, you will print it with the command :

.. code-block:: bash

  lcpymake --script mygraph.py --print

And you will build with :

.. code-block:: bash

  lcpymake --script mygraph.py --build

In other python files, you will write the code of the rules, for instance to call the compiler, and also the code for the scanners.
