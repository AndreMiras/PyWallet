# Change Log

## [Unreleased]

  - Fix app may crash on startup, refs #94
  - Fix app may crash on account deletion, refs #90

## [v20171022]

  - Add flash QR Code support, refs #85

## [v20170920]

  - Fix flaky scrypt test, refs #59
  - Migrate kivyunittest==0.1.8, refs #78
  - Add account alias feature, refs #66
  - Add copy to clipboard feature, refs #84
  - Add release version in Sentry reports

## [v20170909]

  - Add install documentation
  - Add tab key navigation (desktop app), refs #43
  - Disable Sentry in "debug" mode, refs #64
  - Add account deletion feature, refs #51
  - Do not allow empty account password, refs #69
  - Document testing, refs #62
  - Fix account address on small screen, refs #75
  - Fix account address not centered, refs #74
  - Refresh account list after creation, refs #56
  - Add global account selection control, refs #70
  - Use upstream recipes, refs #28
  - Toolbar title refactoring, refs #80
  - Hide advanced account options, refs #53
  - Show version in about, refs #46
  - Fix rounding issues in send page

## [v20170719]

  - Fix crash on send click, refs #63

## [v20170716]

  - Fix crash on empty keystore
  - Introduce UI unit testing, refs #41
  - Run app unit tests in a thread, refs #42
  - Add custon application icon, refs #24
  - Add custon splash screen, refs #25
  - Document release process, refs #47
  - Fix account list overlap, refs #49
  - Sentry error reporting, refs #54
  - Fix Travis isort inconsistencies, refs #57
  - Display changelog in the app, refs #58
  - Introduce APK size reduction, refs #60

## [v20170706]

  - Create new account, refs #9
  - Manage account password, refs #9
  - Run builds in parallel, refs #34
  - Run unit tests from the app, refs #40
  - Use a thread decorator, refs #33
  - Round transaction history, refs #45
  - Fit long address to screen
  - Use toolbar space for dynamic titles
  - Fix broken manage account layout, refs #38
  - Skip pkg-config, refs #39
  - Add coverage testing, refs #32

## [v20170625]

  - Address selection widget fixes
  - Send transaction through Etherscan, refs #21
  - Android build on Travis CI, refs #20
  - Run unlock account & send transaction in a thread
  - Fixes "send" page layout, refs #27

## [v20170621]

  - Travis-CI integration, refs #15
  - Handle ConnectionError gracefully
  - Fetch history in a thread, refs #22
  - Load balance in a thread, refs #23
  - Account selection on overview, refs #17

## [v20170618]

  - Show transactions history, refs #16

## [v20170617]

  - Show default account balance
  - Receive ETH, refs #10
