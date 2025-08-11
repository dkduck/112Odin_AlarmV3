# Commit-ready instructions for GitHub

1. Create a new repository named `112Odin-Alarmer` under your GitHub account (e.g. dkduck).

2. Clone the repo locally and copy all files from this ZIP into the repo root.

3. git add ., git commit -m "Initial release: 112Odin Alarmer v1.2", git push origin main

4. Create a release by tagging a commit, e.g.:

   git tag v1.2.0
   git push origin v1.2.0

5. In GitHub go to Releases → Draft a new release and publish. HACS will detect the release.

6. Optionally enable the GitHub Action by editing `.github/workflows/release.yml` to suit CI needs.
