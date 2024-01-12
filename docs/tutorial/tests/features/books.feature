Feature: Library book searches and book delivery
Scenario: The catalog can be searched by author name.
    Given these books in the catalog
    | Author          | Title                       |
    | Stephen King    | The Shining                 |
    | James Baldwin   | If Beale Street Could Talk  |
    When a name search is performed for Stephen
    Then only these books will be returned
    | Author          | Title                       |
    | Stephen King    | The Shining                 |

