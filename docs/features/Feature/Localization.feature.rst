Scenarios tags could be localized
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

pytest-bdd-ng supports all localizations which Gherkin does:
https://cucumber.io/docs/gherkin/languages/

Scenario:
'''''''''

- Given File "Localized.feature" with content:

  .. code:: gherkin

     #language: pt
     #encoding: UTF-8
     Funcionalidade: Login no Programa
         CenГЎrio: O usuГЎrio ainda nГЈo Г© cadastrado
             Dado que o usuГЎrio esteja na tela de login
             Quando ele clicar no botГЈo de Criar Conta
             EntГЈo ele deve ser levado para a tela de criaГ§ГЈo de conta

- And File "conftest.py" with content:

  .. code:: python

     from pytest_bdd import  given, when, then

     @given("que o usuГЎrio esteja na tela de login")
     def tela_login():
         assert True

     @when("ele clicar no botГЈo de Criar Conta")
     def evento_criar_conta():
         assert True

     @then("ele deve ser levado para a tela de criaГ§ГЈo de conta")
     def tela_criacao_conta():
         assert True

- When run pytest

- Then pytest outcome must contain tests with statuses:

  ====== ======
  passed failed
  ====== ======
  1      0
  ====== ======
