import unasync
from setuptools import setup

setup(
    cmdclass={
        "build_py": unasync.cmdclass_build_py(
            rules=[
                unasync.Rule("/pytest_bdd/_async/", "/pytest_bdd/_sync/"),
            ]
        )
    }
)
