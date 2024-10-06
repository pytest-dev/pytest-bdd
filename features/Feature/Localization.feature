Feature: Scenarios tags could be localized
  pytest-bdd-ng supports all localizations which
  Gherkin does: https://cucumber.io/docs/gherkin/languages/

  Scenario:
      Given File "Localized.feature" with content:
        """gherkin
        #language: pt
        #encoding: UTF-8
        Funcionalidade: Login no Programa
            Cenário: O usuário ainda não é cadastrado
                Dado que o usuário esteja na tela de login
                Quando ele clicar no botão de Criar Conta
                Então ele deve ser levado para a tela de criação de conta
        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd import  given, when, then

        @given("que o usuário esteja na tela de login")
        def tela_login():
            assert True

        @when("ele clicar no botão de Criar Conta")
        def evento_criar_conta():
            assert True

        @then("ele deve ser levado para a tela de criação de conta")
        def tela_criacao_conta():
            assert True
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     0|
