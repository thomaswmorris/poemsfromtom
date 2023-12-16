poems
-----

All of the poems in here are good, or interesting. There are currently 6,967 poems by 445 poets.


usage
-----

The ``poemsfromtom`` package works with a ``Curator``, initialized as 

.. code-block:: python

    import poemsfromtom as poems
    
    curator = poems.Curator()
    
It can get us a random poem by a specified poet

.. code-block:: python
    
    # Load a random poem by Robert Frost
    poem = curator.get_poem(author="robert-frost")
    print(poem.body)
    
or a specified poem by a specified poet

.. code-block:: python
    
    # Load "The Tyger" by William Blake
    poem = curator.get_poem(author="william-blake", title="the-tyger") 
    print(poem.body)

assuming that it is in the database (which you can see as ``curator.poems``). We can also load contextual poems (e.g. so that it loads summer poems during the summer, Christmas poems on Christmas, etc.):

.. code-block:: python
    
    context = poems.utils.get_context() # Just a dictionary
    print(context)
    
    poem = curator.get_poem(context=context) # Loads a contextual poem

Note that if it's summertime, this does not guarantee a summer poem (rather, it only excludes e.g. winter poems and adjusts the likelihood of summer poems to make up for al the times during the year that it isn't summer), though we can force the context if we want:

.. code-block:: python
    
    context = poems.utils.get_context()
    print(context)
    
    # A guaranteed holiday poem, assuming it's a holiday when you run this
    poem = curator.get_poem(context=context, forced_contexts=['holiday']) 

    # A guaranteed seasonal poem
    poem = curator.get_poem(context=context, forced_contexts=['season']) 
    
Unforced contextual poems are sent daily to the listserv. Past poems are on my `website <https://thomaswmorris.com/poems>`_. If you want to be on the listserv, just ask me.