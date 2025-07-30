from setuptools import setup, find_packages

setup(
    name="core",               # Importable as `import core`
    version="0.1.0",
    packages=find_packages(),  # Auto-discovers all packages in Core/
)
