# Limitations and safety-relevant use

This page is the substitute for a hazard report (SWEHB 5.24 is not applicable because nothing here is safety-critical; see the [SMP](../../plan/software-management-plan.md#1-software-classification-self-assessed)). Read it before using any result outside research.

## What the outputs are

- `fm_research`: a status per claim. `certified` means a finite exact check passed under its admitted (`cited`) prerequisites. It does not prove the claim's prose, and `cited` premises are admitted, not proved.
- `fm_mapper`: a deterministic bookkeeping report over judgments **you supplied**. `supported` means support under those judgments at the stated scope. Every paper is `draft_not_scientifically_accepted`.
- `fm_control`, `fm_certificates`, `fm_identifiability`, `fm_enclosures`, `fm_intervals`: exact checks of supplied witnesses or exact enclosures under a stated mathematical model. Each is a conditional mathematical statement about the numbers given.

None of these is an engineering approval, a safety determination, a regulatory compliance check or scientific acceptance.

## What the software does not do

- It does not command or monitor hardware. `fm_control` is arithmetic on supplied numbers for one discrete step of a scalar affine model; it is not a controller or simulator.
- It does not validate a physical model, units or measurements. No dimensional analysis or unit conversion is performed; gauge and absolute pressures, for example, are not distinguished.
- It does not search for witnesses or solve optimization problems. A failed or missing certificate proves nothing about the opposite claim.
- It does not authenticate reviewers or the authors of judgments, and hashes do not authenticate loaded code.
- It does not establish geometry, actual maps or existence from characters and Hom dimensions.

## Data sources and their limits

The only embedded reference table is the SL2(F5) character catalog. Its source, digest and checks are in the [data dictionary §4](../../data/data-dictionary.md#4-reference-data-provenance). Its identification with the group is an assumption recorded in the file itself; the repository records no external bibliographic source. All examples and fixtures are synthetic.

## Use in safety, engineering or regulated decisions

Do not use any output as the sole basis for such a decision. If you give `fm_control`, `fm_enclosures` or `fm_intervals` numbers physical meaning, you must establish model validity, units and measurement uncertainty yourself and check the result against an authoritative engineering method. Such use moves your application to a higher assurance class (Class D analog or above) that this project does not provide.

## Misuse and security considerations

The CLIs read only the files you name and write only fresh paths you name; artifact paths cannot escape their root. The Python APIs trust their in-process caller and are not sandboxes. Bound CPU, memory and time at the process level when handling untrusted input. Report vulnerabilities as described in [SECURITY.md](../../../SECURITY.md).

## Known limitations

| Limitation | Effect | Issue |
|---|---|---|
| `fm_research_commit` records the HEAD of whatever Git repository contains the source tree, or `unknown` | A receipt can name an unrelated commit (defect D1 in the [assurance record](../../assurance/assurance-record.md)) | — |
| Twelve behaviours have no test | Listed in [SRS §9](../../requirements/requirements.md#9-untested-behaviour-requirement-gaps) | — |
| Python 3.10 and 3.11 are not tested | The declared floor may be wrong | — |
| Floats passed to `fm_control` are taken as their exact binary value | `0.1` is not one tenth; use `"0.1"` or `Fraction(1, 10)` | — |
| Resource caps reject some valid inputs | A cap rejection is not a mathematical result | — |
