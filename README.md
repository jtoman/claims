# Claims: Proof Carrying Papers

During the deadline push it's easy to update your implementation but forget to
change some claim in your paper. The claims package helps you track and automatically
verify the claims in your paper to help ensure the practice of good science.

## Use case

Suppose you're working on a verification effort and early in the paper writing process
you make the claim: "We do not assume any axioms." But up against the deadline you
discover that you in fact need to assume some axiom. This by itself may not be a problem,
but now your prose no longer matches your proofs! That's where the claims package comes in.
You first *tag* the claim as follows:

```latex
\claim[no-axioms]{We do not assume any axioms}
```

...and specify a *verifier* like so:

```yaml
no-axioms:
	cmd: "grep -q -R src/ Axiom"
	invert: true
```

In short, `claims` is meant to help ensure natural language assertions do not fall out of
sync with your implementation

## Requirements

* A sufficiently modern LaTeX distribution
* Python 2.7

## Installation

Simply make `claims.sty` available to your latex distribution. For single paper uses,
it suffices to place `claims.sty` in the same folder as your paper source.
`verify-claims.py` can be added to your path, or you can invoke it explicitly.

## Usage

Throughout this README it is assumed the top-level paper source (i.e. the preamble)
is contained in the file `paper.tex`. `claims` is used as follows:

1. Find and tag all claims in the paper, optionally marking any values in the claim needed for verification
2. Specify verifiers for all claims made in your paper
3. Run the latex compiler on the paper source. This produces the ancilliary file `paper.clm`
4. Run the `verify-claims.py` script on the generated `paper.clm`. This will generated `paper.vld` which records which claims have been validated.
5. Recompile the paper. Any remaining false or unverified claims remaining should be investigated (optional).

Steps 1 and 2 are performed as needed as claims are added or changed whereas steps 3-5 should
be integrated into your paper build tool of choice.

## Tagging Claims

In your latex source, enclose all *minor* claims in the `claim` macro:

```latex
\claim[eels]{My hovercraft is full of eels!}
```

The first argument, `eels`, is a unique claim id. This id must be unique throughout
the entire paper. The second argument, `My hovercraft is full of eels!` is the claim
text itself. Claims should be restricted to relatively simple TeX: attempts to include
tables, figures, etc. are not guaranteed to work.

*Major* claims should be enclosed in the `majorclaim` macro:

```latex
\majorclaim[flat-earth]{The earth is totally flat.}
```

The arguments are identical in meaning to the `claim` macro. Currently there
is no practical distinction between minor and major claims beyond documentation.

### Claim references

Claims often reference a specific value of number. For example:

```latex
\claim[eels-ref]{My hovercraft has fewer than 1000 eels}
```

To check this claim, the number of eels in the hovercraft must be comapred to the number
1000 referenced in the text. This value could be hard-coded in the verifier (see below)
but this would make the verification process brittle.

Instead, concrete values needed to verify a claim should be enclosed within the `claimref`
macro. For example

```latex
\claim[eels-ref]{My hovercraft has fewer than \claimref[eel-count]{1000} eels}
```

The first argument, `eel-count` is the reference id and must be unique within each claim.
The second argument is the referenced value and is automatically provided to the `eels-ref`
verifier.

## Specifying Verifiers

Verifiers for claims are specified in a yaml file and are
checked with the `verify-claims.py` script (see below).

The yaml file should be a dictionary: keys are claim ids, and
the entries specify that claim's verififer. 
Each verifier in turn specifies how to execute a program to check
the claim: if the program exits with return code 0 then the claim
is considered true, any other exit code indicates the claim is false.

In the simplest form, a verifier is specified with a command-line string. For example,
to verify the claim `My hovercraft is full of eels`, one might use the verifier:

```yaml
eels: "python ./find-eels.py"
```

Where `find-eels.py` exits with code 0 when the hovercraft is full of eels,
and some non-zero code when no eels are found. Notice the relative
reference in the command-line: verifiers are run in the directory containing the
check file.

### Using Claim References

Claim references are made available using python string substitution in
the verifier command-line. That is, if a claim `foo` contains a reference
`ref` with the value `bar`, then the string `%(ref)s` in `foo`'s verifier
is replaced with `bar`.

For a concrete example, the claim:

```latex
\claim[eels-ref]{My hovercraft has fewer than \claimref[eel-count]{1000} eels.}
```

may have the verifier specification:

```yaml
eels-ref: "python ./verify-eels.py %(eel-count)s"
```

Where verify-eels.py is:

```python
claimed_eels = int(sys.argv[1])
if number_of_eels() < claimed_eels:
  sys.exit(0)
else:
  sys.exit(1)
```

### Customizing Verifier Execution

By default, the verify-claims script:

* interprets verifiers as command lines, not shell commands
* Shell quotes all claim references
* Interprets 0 to indicate a true claim

The above behaviors may be customized with extended verification specifications. In place
of a string, a claim id may map to a yaml dictionary. The dictionary is expected to have
the following format:

* `cmd`: The command-line string/shell command for the verifier (**Required**)
* `shell`: If true, interpret `cmd` as a shell command (**Optional**; default: false)
* `invert`: If true, an exit code of 0 indicates a false claim, non-zero a true claim (**Optional**; default: true)
* `no_quote`: If True, do not quote any claim references. If a list, do not quote the references named in the list. (**Optional**; default: false)

## Verifying the Claims

After compiling `paper.tex`, the `claims` package will generate the file `paper.clm`. To
verify the claims, run `python verify-claims.py ./paper.clm`. If you have specified
the verifiers in `paper.chk` in the same directory as `paper.tex`, no
further arguments are necessary. If you opt not to do this, verify-claims should be
invoked as follows: `python verify-claims.py ./paper.clm /path/to/verify-spec.chk`

After running this command, recompile the paper. Any false claims will be marked as such
in the paper. Any claims without a corresponding verifiers are marked as unverified in the
paper. Feel free to  compile, verify, re-compile as necessary.

## Customizing the Package

`claims` provides a single package option: `paperdeadline` which disables the flagging
of unverified or false claims.

Typesetting or presentation of true, false, and unverified claims may be customized by
overriding the `validclaim`, `unknownclaim`, and `falseclaim` macros respectively. For example,
the `validclaim` macro should be overridden with 

```latex
\def\validclaim[#1]#2{...}
```

Where the first argument is the valid claim id, and the second argument is the claim body.
`unknownclaim` and `falseclaim` are analogously defined.

## Limitations

It is ultimately your responsibility to ensure that the claims made in the paper are faithfully
checked by verifiers. Nothing prevents you from simply using the command "true" to verify
all claims.

Further, currently you must remember to re-run the verification script after adding or changing
a claim. Future versions will (hopefully!) address this pain point.
