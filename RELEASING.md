# Releasing

This is a checklist for releasing a new version of **titiler-stacapi**.

1. Create a release branch named `release/vX.Y.Z`, where `X.Y.Z` is the new version

2. Make sure the [Changelog](CHANGES.md) is up to date with latest changes and release date set

3. Run [`bump-my-version`](https://callowayproject.github.io/bump-my-version/) to update all titiler's module versions: 

    ```
    bump-my-version bump minor --new-version 0.20.0
    ```

4. Push your release branch, create a PR, and get approval

5. Once the PR is merged, create a new (annotated, signed) tag on the appropriate commit. Name the tag `X.Y.Z`, and include `vX.Y.Z` as its annotation message

    ```
    git tag vX.Y.Z
    ```

6. Push your tag to Github, which will kick off the publishing workflow

7. Create a [new release](https://github.com/developmentseed/titiler-stacapi/releases/new) targeting the new tag, and use the "Generate release notes" feature to populate the description. Publish the release and mark it as the latest
