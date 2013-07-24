import unittest, sys, yaml, os

sys.path.append('.')
from maestro import template
from maestro import exceptions

class TestTemplate(unittest.TestCase):

  def testBuild(self):
    # Test correct build    
    config = self._loadFixture("valid_base.yml")
    # This will create a template named test.service.template_test:0.1
    t = template.Template('template_test', config, 'test.service', '0.1')
    self.assertTrue(t.build())

    # Verify the image really exists with docker.
    self.assertIsNotNone(self._findImage(t, t.full_name(), t.version))
    t.destroy()

    # Test correct build  with a tag
    config = self._loadFixture("valid_base_tag.yml")
    t = template.Template('template_test', config, 'test.service', '0.1')
    self.assertTrue(t.build())
    self.assertIsNotNone(self._findImage(t, t.full_name(), t.version))
    t.destroy()

    # Test invalid base image    
    config = self._loadFixture("invalid_base.yml")    
    t = template.Template('template_test', config, 'test.service', '0.1')
    with self.assertRaises(exceptions.TemplateError) as e:
      t.build()
    t.destroy()

    # Test no base image specified
    config = self._loadFixture("no_base.yml")    
    t = template.Template('template_test', config, 'test.service', '0.1')
    with self.assertRaises(exceptions.TemplateError) as e:
      t.build()
    t.destroy()

  def testBuildDockerfile(self):
    # Test correct build using a minimal Dockerfile
    config = self._loadFixture("valid_dockerfile.yml")     
    t = template.Template('template_test', config, 'test.service', '0.1')
    self.assertTrue(t.build())
    t.destroy()

    # Test error on incorrectly formatted Dockerfile
    config = self._loadFixture("invalid_dockerfile.yml")    
    t = template.Template('template_test', config, 'test.service', '0.1')
    with self.assertRaises(exceptions.TemplateError) as e:
      t.build()
    t.destroy()

    # Test error on incorrect format for buildspec
    config = self._loadFixture("invalid_buildspec.yml") 
    t = template.Template('template_test', config, 'test.service', '0.1')
    with self.assertRaises(exceptions.TemplateError) as e:
      t.build()
    t.destroy()

  def testBuildUrl(self):
    # Test correct build using a minimal Dockerfile
    config = self._loadFixture("valid_build_url.yml")
    t = template.Template('template_test', config, 'test.service', '0.1')
    self.assertTrue(t.build())
    t.destroy()
    
  def testDestroy(self):    
    config = self._loadFixture("valid_base.yml")
    t = template.Template('template_test', config, 'test.service', '0.1')
    self.assertTrue(t.build())

    # Make sure the image is there
    self.assertIsNotNone(self._findImage(t, t.full_name(), t.version))
    t.destroy()
    # Now make sure it's gone
    self.assertIsNone(self._findImage(t, t.full_name(), t.version))


  def _loadFixture(self, name):
    return yaml.load(file(os.path.join(os.path.dirname(__file__), "fixtures/template", name), "r"))

  def _findImage(self, t, name, tag="latest"):
    result =  t.docker_client.images(name=name)

    for image in result:
      if image['Tag'] == tag:
        return image['Id']
    return None
    
if __name__ == '__main__':
  unittest.main()