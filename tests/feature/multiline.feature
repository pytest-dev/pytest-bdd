Scenario: Multiline step using sub indentation wrong indent
    Given I have a step with:
        Some

    Extra
    Lines
    Then the text should be parsed with correct indentation
