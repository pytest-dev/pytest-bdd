import json
import os
from unittest.mock import patch

import pytest
from attr import asdict
from attr.exceptions import NotAnAttrsClassError
from pluggy import HookimplMarker
from pydantic import BaseModel as PydanticBaseModel

from pytest_bdd.compatibility.allure import ALLURE_INSTALLED
from pytest_bdd.compatibility.pytest import PYTEST81

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

        self.allure_plugin_name = None
        self.pytest_plugin_name = None

    @classmethod
    def register_if_allure_accessible(cls, config):
        pluginmanager = config.pluginmanager
        allure_accessible = pluginmanager.hasplugin("allure_pytest") and config.option.allure_report_dir
        if allure_accessible and not PYTEST81:
            allure_plugin_manager.get_plugins()

            listener = next(
                filter(lambda plugin: isinstance(plugin, AllureListener), allure_plugin_manager.get_plugins())
            )

            bdd_listener = cls(listener.allure_logger, listener._cache)
            bdd_listener.allure_plugin_name = allure_plugin_manager.register(bdd_listener)
            bdd_listener.pytest_plugin_name = pluginmanager.register(bdd_listener)
            return bdd_listener

    @hookimpl(hookwrapper=True)
    def report_result(self, result):
        def patched_asdict(*args, recurse=True, value_serializer=None, **kwargs):
            def patched_value_serializer(instance, field, value):
                if isinstance(value, PydanticBaseModel):
                    # Maybe possible to speedup; Some values are not serialized when used value.dict()
                    return json.loads(value.model_dump_json())
                elif value_serializer is not patched_value_serializer:
                    return value_serializer(instance, field, value)
                else:
                    if recurse:
                        try:
                            return patched_asdict(
                                value, *args[1:], recurse=True, value_serializer=patched_value_serializer, **kwargs
                            )
                        except NotAnAttrsClassError:
                            return value
                    else:
                        return value

            if value_serializer is None:
                value_serializer = patched_value_serializer

            return asdict(*args, value_serializer=patched_value_serializer, **kwargs)

        with patch("allure_commons.logger.asdict", new=patched_asdict):
            yield

    def unregister(self, config):
        pluginmanager = config.pluginmanager
        allure_accessible = pluginmanager.hasplugin("allure_pytest") and config.option.allure_report_dir
        if allure_accessible:
            allure_plugin_manager.unregister(name=self.allure_plugin_name)
            pluginmanager.unregister(name=self.pytest_plugin_name)

    @pytest.hookimpl
    def pytest_bdd_before_step_call(self, request, feature, scenario, step, step_func, step_func_args, step_definition):
        """Called before step function is set up."""
        step_definition.func = StepContext(f"{step.keyword} {step.text}", step_func_args)(step_func)

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
