Feature: Datatables

  Scenario Outline: I use datatables
    Given the following users exist:
      | name   | email              | twitter         |
      | Aslak  | aslak@cucumber.io  | @aslak_hellesoy |
      | Julien | julien@cucumber.io | @jbpros         |
      | Matt   | matt@cucumber.io   | @mattwynne      |
    Then I should see the following names:
      | name   |
      | Aslak  |
      | Julien |
      | Matt   |


  Scenario Outline: I use datatables for emails
    Given the following users exist:
      | name   | email              | twitter         |
      | Aslak  | aslak@cucumber.io  | @aslak_hellesoy |
      | Julien | julien@cucumber.io | @jbpros         |
      | Matt   | matt@cucumber.io   | @mattwynne      |
    Then I should see the following emails:
      | email  |
      | aslak@cucumber.io  |
      | julien@cucumber.io |
      | matt@cucumber.io   |
