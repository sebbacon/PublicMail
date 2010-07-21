import os, shutil, sys, unittest
 
# Look for coverage.py in __file__/lib as well as sys.path
sys.path = [os.path.join(os.path.dirname(__file__), "lib")] + sys.path
 
import coverage
from django.test.simple import run_tests as django_test_runner
 
from django.conf import settings
 
def run_tests(*args, **kwargs):
  """Custom test runner.  Follows the django.test.simple.run_tests()
  interface."""
  coverage.use_cache(0) # Do not cache any of the coverage.py stuff
  coverage.start()
 
  test_results = django_test_runner(*args, **kwargs)
 
  # Stop code coverage after tests have completed
  coverage.stop()
 
  # Print code metrics header
  print ''
  print '----------------------------------------------------------------------'
  print ' Unit Test Code Coverage Results'
  print '----------------------------------------------------------------------'
 
  # Report code coverage metrics
  coverage_modules = []
  for module in settings.COVERAGE_MODULES:
      coverage_modules.append(__import__(module, globals(), locals(), ['']))
 
  coverage.report(coverage_modules, show_missing=1)
 
  # Print code metrics footer
  print '----------------------------------------------------------------------'
  return test_results
 
