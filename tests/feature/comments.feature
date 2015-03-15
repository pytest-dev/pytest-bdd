Scenario: Comments
    # Comment
    Given I have a bar

Scenario: Strings that are not comments
    Given comments should be at the start of words
    Then this is not a#comment
    And this is not "#acomment"
