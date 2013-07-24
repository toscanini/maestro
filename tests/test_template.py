import unittest, sys, yaml
sys.path.append('.')
from maestro import template
from maestro import exceptions

class TestTemplate(unittest.TestCase):
  def testBuild(self):
    # Test correct build    
    config = yaml.load("""
      base_image: ubuntu
      config:
        command: /bin/bash
        detach: true    
    """)
    
    # This will create a template named test.service.template_test:0.1
    t = template.Template('template_test', config, 'test.service', '0.1')
    self.assertTrue(t.build())

    # Test invalid base image    
    config = yaml.load("""
      base_image: ubuntu2
      config:
        command: /bin/bash
        detach: true    
    """)
    
    t = template.Template('template_test', config, 'test.service', '0.1')
    with self.assertRaises(exceptions.TemplateError) as e:
      t.build()

    # Test no base image specified
    config = yaml.load("""
      config:
        command: /bin/bash
        detach: true    
    """)
    
    t = template.Template('template_test', config, 'test.service', '0.1')
    with self.assertRaises(exceptions.TemplateError) as e:
      t.build()

  def testBuildDockerfile(self):
    # Test correct build using a minimal Dockerfile
    config = yaml.load("""
      base_image: ubuntu
      config:
        command: /bin/bash
        detach: true    
      buildspec:
        dockerfile: |
          FROM ubuntu        
    """)
    
    t = template.Template('template_test', config, 'test.service', '0.1')
    self.assertTrue(t.build())


    # Test error on incorrectly formatted Dockerfile
    config = yaml.load("""
      base_image: ubuntu
      config:
        command: /bin/bash
        detach: true    
      buildspec:
        dockerfile: |
          FRO ubuntu        
    """)
    
    t = template.Template('template_test', config, 'test.service', '0.1')
    with self.assertRaises(exceptions.TemplateError) as e:
      t.build()

    # Test error on incorrect format for buildspec
    config = yaml.load("""
      base_image: ubuntu
      config:
        command: /bin/bash
        detach: true    
      buildspec:
    """)
    t = template.Template('template_test', config, 'test.service', '0.1')
    with self.assertRaises(exceptions.TemplateError) as e:
      t.build()

  def testBuildUrl(self):
      # Test correct build using a minimal Dockerfile
    config = yaml.load("""
      base_image: ubuntu
      config:
        command: /bin/bash
        detach: true    
      buildspec:
        url: github.com/toscanini/maestro-dockerfile-test
    """)
    
    t = template.Template('template_test', config, 'test.service', '0.1')
    self.assertTrue(t.build())
    

if __name__ == '__main__':
  unittest.main()