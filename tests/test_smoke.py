# Test de humo: compila el arbol Python y valida estructura minima.
import os
import py_compile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Smoke(unittest.TestCase):
    def test_readme(self):
        p = os.path.join(ROOT, 'README.md')
        self.assertTrue(os.path.exists(p), 'falta README.md')
        with open(p, encoding='utf-8', errors='ignore') as f:
            self.assertGreaterEqual(len(f.read()), 500)

    def test_python_compila(self):
        n = 0
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '.venv', '__pycache__')]
            for f in files:
                if f.endswith('.py'):
                    py_compile.compile(os.path.join(base, f), doraise=True)
                    n += 1
        self.assertGreater(n, 0, 'no hay modulos Python')


if __name__ == '__main__':
    unittest.main()
