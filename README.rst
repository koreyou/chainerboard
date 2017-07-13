.. -*- coding: utf-8; -*-

An unofficial visualization tool for `chainer <https://chainer.org/>`_, inspired by `tensorboard <https://www.tensorflow.org/get_started/summaries_and_tensorboard>`_. The toolkit allows visualization of log from ``chainer.extensions.LogReport``.

Example usage:

.. code:: python

    model = L.Classifier(MyModel())

    optimizer = chainer.optimizers.Adam()
    optimizer.setup(model)

    train = create_my_data()
    train_iter = chainer.iterators.SerialIterator(train, batchsize)

    updater = training.StandardUpdater(train_iter, optimizer)
    trainer = training.Trainer(updater, (epochs, 'epoch'), out='path/to/output')

    trainer.extend(extensions.LogReport(log_name='my_log_data')))
    # optional; allows visualization of parameters
    trainer.extend(extensions.ParameterStatistics(model))

    # Run the training
    trainer.run()


and point chainerboard at the output log file to start local http server.

.. code:: bash

   chainerboard path/to/output/my_log_name


now open http://localhost:6006/ to view the log.


.. warning:: The author of this project is not a professional web
    programmer. Never use the project on remote server since it may
    impose serious security risks.



Development
============

To setup development environment:

.. code:: bash

     pip install -r requirements.txt


For testing,

.. code:: bash

     tox

Build document

.. code:: bash

     python setup.py build_sphinx
