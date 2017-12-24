.. -*- coding: utf-8; -*-


CHANGELOG
=============

v0.1.5
-------------

* Feature:

  * Compatibility with Python 3 (#14)
  * Quiettend log level (#11)
  * Added `--version` to CLI (#7)
  * Added help message to CLI

* Bugfix:

  * Detect changes in irrerelvant files (#10)


v0.1.4
-------------

* Bugfix:

  * Auto-update was not working
  * It was occasionally causing OSError (#5)


v0.1.3
-------------

* Bugfix:

  * Hot fix for a syntactic bug introduced in v0.1.2


v0.1.2
-------------

* Bugfix:

  * Plotting fails when 'Infinity' is present (#2)

v0.1.1
-------------

* Downgraded to more stable bootstrap 3
* Connection error (distruption) is now handled more gracefully.
* Prettified front end app.

v0.1.0
-------------

* First alpha release.
* Basic visualization of accuracy and loss.
* Plot visualization using Plotly.js.
* Visualization of histograms.
* Parsing of log data from chainer's LogReport
* Log file watching using watchdog.
* Real time updating using ajax (via angularJS).
* Documentation using Sphinx.
