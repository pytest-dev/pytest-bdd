Feature: Юнікодні символи

    Scenario: Кроки в .feature файлі містять юнікод
        Given у мене є рядок який містить 'якийсь контент'
        Then I should see that the string equals to content 'якийсь контент'

    Scenario: Steps in .py file have unicode
        Given there is an other string with content 'якийсь контент'
        Then I should see that the other string equals to content 'якийсь контент'

    Scenario: Given names have unicode types
        Given I have an alias with a unicode type for foo
        Then foo should be "foo"
