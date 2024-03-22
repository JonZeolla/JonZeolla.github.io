# Future testing improvements

1. Allow the region to be specified when testing.
1. Add pipeline support (headless=True).
1. Fix it so we don't need to skip any tests (currently using class: skip-tests for interactive, multi-code block step by steps). Run goss/dgoss remotely?
1. Improve the cleanup/teardown to be more pytest native.
1. Add tests inline, hidden in the labs. Extract and then run them interleaved with the visible code blocks. Maybe goss/dgoss?
