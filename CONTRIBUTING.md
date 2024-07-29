# Contributing to idc-index

There are many ways to contribute to idc-index, with varying levels of effort.
Do try to look through the [documentation](idc-index-docs) first if something is
unclear, and let us know how we can do better.

- Ask a question on the [IDC forum][idc-forum]
- Use [idc-index issues][idc-index-issues] to submit a feature request or bug,
  or add to the discussion on an existing issue
- Submit a [Pull Request](https://github.com/ImagingDataCommons/idc-index/pulls)
  to improve idc-index or its documentation

We encourage a range of Pull Requests, from patches that include passing tests
and documentation, all the way down to half-baked ideas that launch discussions.

## The PR Process, Circle CI, and Related Gotchas

### How to submit a PR ?

If you are new to idc-index development and you don't have push access to the
repository, here are the steps:

1. [Fork and clone](https://docs.github.com/get-started/quickstart/fork-a-repo)
   the repository.
2. Create a branch dedicated to the feature/bugfix you plan to implement (do not
   use `main` branch - this will complicate further development and
   collaboration)
3. [Push](https://docs.github.com/get-started/using-git/pushing-commits-to-a-remote-repository)
   the branch to your GitHub fork.
4. Create a
   [Pull Request](https://github.com/ImagingDataCommons/idc-index/pulls).

This corresponds to the `Fork & Pull Model` described in the
[GitHub collaborative development](https://docs.github.com/pull-requests/collaborating-with-pull-requests/getting-started/about-collaborative-development-models)
documentation.

When submitting a PR, the developers following the project will be notified.
That said, to engage specific developers, you can add `Cc: @<username>` comment
to notify them of your awesome contributions. Based on the comments posted by
the reviewers, you may have to revisit your patches.

### How to efficiently contribute ?

We encourage all developers to:

- set up pre-commit hooks so that you can remedy various formatting and other
  issues early, without waiting for the continuous integration (CI) checks to
  complete: `pre-commit install`

- add or update tests. You can see current tests
  [here](https://github.com/ImagingDataCommons/idc-index/tree/main/tests). If
  you contribute new functionality, adding test(s) covering it is mandatory!

- you can run individual tests from the root repository using the following
  command: `python -m unittest -vv tests.idcindex.TestIDCClient.<test_name>`

### How to write commit messages ?

Write your commit messages using the standard prefixes for commit messages:

- `BUG:` Fix for runtime crash or incorrect result
- `COMP:` Compiler error or warning fix
- `DOC:` Documentation change
- `ENH:` New functionality
- `PERF:` Performance improvement
- `STYLE:` No logic impact (indentation, comments)
- `WIP:` Work In Progress not ready for merge

The body of the message should clearly describe the motivation of the commit
(**what**, **why**, and **how**). In order to ease the task of reviewing
commits, the message body should follow the following guidelines:

1. Leave a blank line between the subject and the body. This helps `git log` and
   `git rebase` work nicely, and allows to smooth generation of release notes.
2. Try to keep the subject line below 72 characters, ideally 50.
3. Capitalize the subject line.
4. Do not end the subject line with a period.
5. Use the imperative mood in the subject line (e.g.
   `BUG: Fix spacing not being considered.`).
6. Wrap the body at 80 characters.
7. Use semantic line feeds to separate different ideas, which improves the
   readability.
8. Be concise, but honor the change: if significant alternative solutions were
   available, explain why they were discarded.
9. If the commit refers to a topic discussed on the [IDC forum][idc-forum], or
   fixes a regression test, provide the link. If it fixes a compiler error,
   provide a minimal verbatim message of the compiler error. If the commit
   closes an issue, use the
   [GitHub issue closing keywords](https://docs.github.com/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue).

Keep in mind that the significant time is invested in reviewing commits and
_pull requests_, so following these guidelines will greatly help the people
doing reviews.

These guidelines are largely inspired by Chris Beam's
[How to Write a Commit Message](https://chris.beams.io/posts/git-commit/) post.

### How to integrate a PR ?

Getting your contributions integrated is relatively straightforward, here is the
checklist:

- All tests pass
- Consensus is reached. This usually means that at least two reviewers approved
  the changes (or added a `LGTM` comment) and at least one business day passed
  without anyone objecting. `LGTM` is an acronym for _Looks Good to Me_.
- To accommodate developers explicitly asking for more time to test the proposed
  changes, integration time can be delayed by few more days.
- If you do NOT have push access, a core developer will integrate your PR. If
  you would like to speed up the integration, do not hesitate to add a reminder
  comment to the PR

### Automatic testing of pull requests

Every pull request is tested automatically using GitHub Actions each time you
push a commit to it. The GitHub UI will restrict users from merging pull
requests until the CI build has returned with a successful result indicating
that all tests have passed.

[idc-forum]: https://discourse.canceridc.dev
[idc-index-issues]: https://github.com/ImagingDataCommons/idc-index/issues
[idc-index-docs]: https://idc-index.readthedocs.io/
