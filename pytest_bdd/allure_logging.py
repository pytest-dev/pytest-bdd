from __future__ import annotations

import os

import pytest
from attr import asdict
from pluggy import HookimplMarker

from pytest_bdd.model import Feature, Scenario, Step, Tag
from pytest_bdd.typing.allure import ALLURE_INSTALLED

if ALLURE_INSTALLED:
    from allure_commons import hookimpl
    from allure_commons import plugin_manager as allure_plugin_manager
    from allure_commons._allure import StepContext
    from allure_commons.model2 import Label, Parameter, Status, TestStepResult
    from allure_commons.types import LabelType
    from allure_commons.utils import md5, now, platform_label
    from allure_pytest.listener import AllureListener
else:
    hookimpl = HookimplMarker("allure")


class AllurePytestBDD:
    def __init__(self, allure_logger, allure_cache):
        self.allure_logger = allure_logger
        self._cache = allure_cache

    @classmethod
    def register_if_allure_accessible(cls, config):
        pluginmanager = config.pluginmanager
        allure_accessible = pluginmanager.hasplugin("allure_pytest") and config.option.allure_report_dir
        if allure_accessible:
            allure_plugin_manager.get_plugins()

            listener = next(
                filter(lambda plugin: isinstance(plugin, AllureListener), allure_plugin_manager.get_plugins())
            )

            bdd_listener = cls(listener.allure_logger, listener._cache)
            allure_plugin_manager.register(bdd_listener)
            pluginmanager.register(bdd_listener)

    @hookimpl(hookwrapper=True)
    def report_result(self, result):
        recomposable_features = []

        def decompose_scenario_or_feature(attr, value):
            if isinstance(value, (Tag, Step, Scenario, Feature)):
                if isinstance(value, Feature):
                    recomposable_features.append(value)
                value.decompose()
            return True

        asdict(result, filter=decompose_scenario_or_feature)

        yield

        while recomposable_features:
            recomposable_features.pop().compose()

    @pytest.hookimpl
    def pytest_bdd_before_step_call(self, request, feature, scenario, step, step_func, step_func_args, step_definition):
        """Called before step function is set up."""
        step_definition.func = StepContext(f"{step.keyword} {step.name}", step_func_args)(step_func)

    @pytest.hookimpl
    def pytest_bdd_before_scenario(self, request, feature, scenario):

        scenario_result_uuid = self._cache.get(scenario)
        test_result_uuid = self._cache.get(request.node.nodeid)

        if not scenario_result_uuid:
            scenario_result_uuid = self._cache.push(scenario)

        self.allure_logger.start_step(test_result_uuid, scenario_result_uuid, TestStepResult())

        scenario_result = self.allure_logger.get_test(scenario_result_uuid)
        test_result = self.allure_logger.get_item(test_result_uuid)
        full_name = self.get_full_name(feature, scenario)
        name = self.get_name(request.node, scenario)

        scenario_result.fullName = full_name
        scenario_result.name = name
        scenario_result.start = now()
        scenario_result.historyId = md5(request.node.nodeid)
        test_result.labels.append(Label(name=LabelType.FRAMEWORK, value="pytest-bdd"))
        test_result.labels.append(Label(name=LabelType.LANGUAGE, value=platform_label()))
        test_result.labels.append(Label(name=LabelType.FEATURE, value=feature.name))
        scenario_result.parameters = self.get_params(request.node)

    @pytest.hookimpl
    def pytest_bdd_after_scenario(self, request, feature, scenario):
        scenario_result_uuid = self._cache.get(scenario)
        scenario_result = self.allure_logger.get_item(scenario_result_uuid)
        scenario_result.stop = now()
        self.allure_logger.stop_step(scenario_result_uuid)

    @pytest.hookimpl
    def pytest_bdd_step_func_lookup_error(self, request, feature, scenario, step, exception):
        scenario_result_uuid = self._cache.get(scenario)
        scenario_result = self.allure_logger.get_item(scenario_result_uuid)
        scenario_result.status = Status.BROKEN
        scenario_result.status_details = exception
        self.allure_logger.stop_step(scenario_result_uuid)

    @staticmethod
    def get_params(node):
        if hasattr(node, "callspec"):
            params = node.callspec.params
            return [Parameter(name=name, value=value) for name, value in params.items()]

    @staticmethod
    def get_name(node, scenario):
        if hasattr(node, "callspec"):
            parts = node.nodeid.rsplit("[")
            return f"{scenario.name} [{parts[-1]}"
        return scenario.name

    @staticmethod
    def get_full_name(feature, scenario):
        feature_path = os.path.normpath(feature.rel_filename)
        return f"{feature_path}:{scenario.name}"
