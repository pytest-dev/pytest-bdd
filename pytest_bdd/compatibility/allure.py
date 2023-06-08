try:
    import allure_commons
    import allure_pytest
except ImportError:
    ALLURE_INSTALLED = False
else:
    ALLURE_INSTALLED = True
