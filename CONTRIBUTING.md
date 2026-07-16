# Contributing

Contributions are welcome in four bounded areas: country profiles, executable rules, validators,
and benchmark cases.

Every rule contribution must include a stable identifier, version, target, constraint, severity,
and source evidence. State the source licence. Proposed rules from automated extraction are not
accepted as authoritative until a domain expert reviews them.

Every validator change must include a clean case, a failing case, frozen expected issue keys, and a
description of false-positive risks. Repair logic must declare its risk class and may not bypass the
approval boundary.

Run `make verify` before submitting a change. Do not place restricted source documents, production
credentials, personal data, or non-redistributable national mapping data in the repository.
