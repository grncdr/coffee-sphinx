from distutils.core import setup

if __name__ == '__main__':
    setup(name='sphinxcontrib-coffee',
          version='0.0.1',
          author="Stephen Sugden",
          author_email="stephen@betsmartmedia.com",
          packages=['sphinxcontrib',
                    'sphinxcontrib.coffeedomain'],
          package_dir={
              'sphinxcontrib':              'src/sphinxcontrib',
              'sphinxcontrib.coffeedomain': 'src/sphinxcontrib/coffeedomain'
          },
          package_data={
              'sphinxcontrib.coffeedomain': ['nodes_to_json.coffee'],
          })
