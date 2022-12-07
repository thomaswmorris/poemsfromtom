

Usage
-----

The ``poetry`` package works with a curator, initialized as 

.. code-block:: python

    import poetry
    
    curator = poetry.Curator()
    
We can get a random poem from a specified poet:

.. code-block:: python
    
    poem = curator.get_poem(author="frost") # Robert Frost
    print(poem.body)
    
or a specified poem:

.. code-block:: python
    
    poem = curator.get_poem(author="blake", title="THE TYGER") # "The Tyger" by William Blake
    print(poem.body)

We can additionally 

.. code-block:: python
    
    context = poetry.utils.get_context()
    
    # Loads a contextual poem, e.g. Christmas poems on Christmas and summer poems during the summer
    poem = curator.get_poem(context=context, weight_schemes=['context']) 
    print(poem.body)
    
Contextual poems are sent daily to the listserv, which can be found `here <https://thomaswmorris.github.io/poems>`_. If you want to be on the email list, just ask me. 
