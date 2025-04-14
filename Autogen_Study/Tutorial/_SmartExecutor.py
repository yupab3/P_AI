import ast
import os
import sys
import importlib.util
from autogen.coding.jupyter import JupyterCodeExecutor


def extract_packages_from_code(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    packages = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                packages.add(n.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                packages.add(node.module.split('.')[0])
    return list(packages)


def is_package_installed(pkg_name: str) -> bool:
    return importlib.util.find_spec(pkg_name) is not None


def install_missing_packages(packages: list[str]):
    for pkg in packages:
        if not is_package_installed(pkg):
            print(f"🔧 Installing {pkg} ...")
            os.system(f"pip install {pkg}")  # mamba 사용하려면 여기만 바꾸면 됨


class SmartJupyterExecutor(JupyterCodeExecutor):
    def execute_code(self, code: str, **kwargs):
        packages = extract_packages_from_code(code)
        external_packages = [p for p in packages if not is_package_installed(p)]
        if external_packages:
            print(f"📦 Detected external packages: {external_packages}")
            install_missing_packages(external_packages)
        return super().execute_code(code, **kwargs)