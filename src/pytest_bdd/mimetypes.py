from enum import Enum


class Mimetype(Enum):
    gherkin_plain = "text/x.cucumber.gherkin+plain"
    markdown = "text/x.cucumber.gherkin+markdown"
    struct_bdd_yaml = "application/x.struct_bdd+yaml"
    struct_bdd_hocon = "application/x.struct_bdd+hocon"
    struct_bdd_json5 = "application/x.struct_bdd+json5"
    struct_bdd_json = "application/x.struct_bdd+json"
    struct_bdd_hjson = "application/x.struct_bdd+hjson"
    struct_bdd_toml = "application/x.struct_bdd+toml"
    python = "text/x-python"
