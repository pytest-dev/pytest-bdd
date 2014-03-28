Scenario: Multiline step using sub indentation
    Given I have a step with:
        Some
        Extra
        Lines
    Then the text should be parsed with correct indentation
