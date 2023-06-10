try:
    from pytest_bdd.struct_bdd.parser import StructBDDParser
except ImportError:
    STRUCT_BDD_INSTALLED = False
else:
    STRUCT_BDD_INSTALLED = True
