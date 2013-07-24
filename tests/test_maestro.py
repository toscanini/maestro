import unittest, sys
sys.path.append('.')
import maestro

class TestMaestro(unittest.TestCase):
  def testCreateGlobalEnvironment(self):
    maestro.init_environment()
    
  def testCreateLocalEnvironment(self):
    env = maestro.init_environment("testEnvironment")

    self.assertIsNotNone(env)
  
  def testCreateExistingEnvironment(self):
    maestro.init_environment()
  
  def testGetEnvironment(self):
    pass

  def testListEnvironment(self):
    pass

  def testDestroyLocalEnvironment(self):
    pass

  def testDestroyGlobalEnvironment(self):
    pass

if __name__ == '__main__':
    unittest.main()