import sys, subprocess, os, yaml

def detex_claim(claim_text):
    proc = subprocess.Popen(["detex", "-s", "-"], stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    (out, err) = proc.communicate(claim_text)
    assert proc.returncode == 0
    return out
    
def parse_claims(of):
    claims = {}
    made_claims = {}
    lines = []
    with open(of, 'r') as f:
        for l in f:
            if len(l.strip()) == 0:
                continue
            lines.append(l.strip())
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("@CLAIM@"):
            break
        if not (l.startswith("minor ") or l.startswith("major ")):
            raise RuntimeError("Malformed claim file: " + l)
        (claim_type, claim_id) = l.split(" ", 1)
        i+=1
        num_params = int(lines[i])
        p_count = 0
        params = {}
        while p_count < num_params:
            key = lines[i+1]
            value = detex_claim(lines[i+2])
            i+=2
            p_count+=1
            params[key]=value
        i+=1
        claims[claim_id] = { "type": claim_type, "params": params }
    while i < len(lines):
        l = lines[i]
        if not l.startswith("@CLAIM@"):
            raise RuntimeError("Malformed claim file: " + l)
        claim_id = l[len("@CLAIM@"):]
        assert claim_id in claims, claim_id
        i+=1
        claim_text = ""
        while i < len(lines) and not lines[i].startswith("@CLAIM@"):
            claim_text += lines[i]
            i+=1
        made_claims[claim_id] = claim_text
    return {"def": claims, "made": made_claims}

def parse_checkers(c_file):
    with open(c_file, "r") as f:
        check_def = yaml.load(f)
    to_ret = {}
    for (k,v) in check_def.iteritems():
        if type(v) is str:
            to_ret[k] = {"cmd": v}
        elif type(v) is dict and "cmd" in v and type(v["cmd"]) is str:
            to_ret[k] = v
        else:
            raise RuntimeError("Malformed checker specification")
    return to_ret

def check_claims(claim_dir, claims, checkers):
    results = {}
    for claim_id in claims["made"].iterkeys():
        if claim_id not in checkers:
            print "WARNING: claim", claim_id, "has no checker defined and is UNVERIFIED"
            results[claim_id] = None
            continue
        import shlex, pipes
        checker_spec = checkers[claim_id]
        cmd = checker_spec["cmd"]
        params = None
        if "no_quote" in checker_spec and checker_spec["no_quote"] is True:
            params = claims["def"][claim_id]["params"]
        else:
            no_quote = set(checker_spec["no_quote"]) \
                       if "no_quote" in checker_spec and checker_spec["no_quote"] is not False \
                          else set()
            quoted_params = {}
            for (k,v) in claims["def"][claim_id]["params"].iteritems():
                if k in no_quote:
                    quoted_params[k] = v
                else:
                    quoted_params[k] = pipes.quote(v)
            params = quoted_params
        kw_params = {}
        if "shell" in checker_spec and checker_spec["shell"] is True:
            kw_params["shell"] = True
            cmd_arg = cmd % params
        else:
            command_string = shlex.split(cmd)
            cmd_arg = [ arg % params for arg in command_string ]
        check_call = subprocess.Popen(cmd_arg, cwd = claim_dir, stdout = subprocess.PIPE, stderr = subprocess.PIPE, **kw_params)
        (check_stdout, check_stderr) = check_call.communicate()
        success = check_call.returncode == 0
        if "invert" in checker_spec and checker_spec["invert"] is True:
            success = not success
        if success:
            results[claim_id] = True
        else:
            print "WARNING: verification of", claim_id, "FAILED!"
            print " >>> Claim text:"
            print " ", detex_claim(claims["made"][claim_id])
            print " >>> Verifier stdout:"
            if len(check_stdout) > 0:
                print check_stdout
            print " >>> Verifier stderr:"
            if len(check_stderr) > 0:
                print check_stderr
            results[claim_id] = False
    return results

def write_results(valid_file, results):
    with open(valid_file, "w") as f:
        for (k,v) in results.iteritems():
            if v is None:
                continue
            elif v is True:
                print >> f, '\expandafter\def\csname vld@%s\endcsname{2}' % k
            else:
                print >> f, '\expandafter\def\csname vld@%s\endcsname{1}' % k

if len(sys.argv) == 1:
    print "Usage: " + sys.argv[0] + " claim-file [verify-file]"
    sys.exit(1)

claims = parse_claims(sys.argv[1])
if len(sys.argv) == 3:
    check_def_file = sys.argv[2]
else:
    if not sys.argv[1].endswith(".clm"):
        print "Could not infer checker file from claim file " + sys.argv[1] + ", please specify"
        sys.exit(1)
    check_def_file = sys.argv[1][:-4] + ".chk"

if not os.path.exists(check_def_file):
    claim_checkers = {}
else:
    claim_checkers = parse_checkers(check_def_file)

check_results = check_claims(os.path.realpath(os.path.dirname(sys.argv[1])), claims, claim_checkers)

validation_file = sys.argv[1][:-4] + ".vld"
write_results(validation_file, check_results)
