Synchronization algorithm
=========================

The synchronization is performed over a few steps:

1. Fetch all users/groups from the directory, mapping them to
   :class:`datastructs.Account` / :class:`datastructs.Group` objects;
   see :func:`sources.BaseSource.fetch_users` and :func:`sources.BaseSource.fetch_groups`.

2. For each sink, fetch its list of users/groups, mapping them to (partial)
   :class:`datastructs.Account` / :class:`datastructs.Group` objects;
   see :func:`sinks.BaseSink.fetch_users` and :func:`sinks.BaseSink.fetch_groups`.

3. Match user ids from both lists (don't look at internal data changes)

4. For each object, compute the new remote structure (happens in
   :meth:`sinks.BaseSink.map_user` and :meth:`sinks.BaseSink.map_group`)

5. Send updated objects to the remote

.. note:: This algorithm fails if one needs to detect updates to write-only fields
