Scenario: Steps in .feature file have unicode
    Given there is a string with content 'с каким-то контентом'
    Then I should see that the string equals to content 'с каким-то контентом'


Scenario: Steps in .py file have unicode
    Given there is an other string with content 'с каким-то контентом'
    Then I should see that the other string equals to content 'с каким-то контентом'
