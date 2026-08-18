# Open-source Checklist

Repository-owner decisions required before publication:

- [x] **License decision:** MIT selected; the tracked `LICENSE` contains the MIT text and copyright notice.
- [ ] **Secret scan:** review tracked history and current files with an approved scanner; rotate anything ever exposed.
- [ ] **Dependency-license review:** review direct and transitive Python package licenses for the intended distribution.
- [ ] **Dataset review:** confirm attribution, source terms, and redistribution rights; resolve CodeContests and TACO upstream caveats.
- [ ] **Documentation review:** verify commands, screenshots, support expectations, and privacy statements on a clean machine.
- [ ] **Security contact:** enable GitHub private vulnerability reporting and decide a private fallback contact. Do not publish a fake address.
- [ ] **CI/test decision:** decide which Python/OS matrix and required checks protect `main`.
- [ ] **Repository visibility:** confirm excluded local databases, datasets, environments, caches, and tool output before switching to public.
- [ ] **Release/versioning:** decide tag ownership, release notes, compatibility policy, and whether `0.1.0` is ready for publication.

Preparation is not authorization to publish, push, release, or change repository visibility.
