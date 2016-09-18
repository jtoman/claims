import subprocess, shutil, os.path, re, sys

THIS_DIR = os.path.realpath(os.path.dirname(sys.argv[0]))
ROOT_DIR = os.path.realpath(THIS_DIR + "/..")

class TestFailedError(RuntimeError):
    def __init__(self, message, output):
        RuntimeError.__init__(self, message)
        self.output = output

def update_accum(accum, cmd, o, e):
    c_string = str(cmd)
    accum[0] += " >>> Stdout of " + c_string + ":\n"
    accum[0] += o
    accum[1] += " >>> Stderr of " + c_string + ":\n"
    accum[1] += e

def run_subprocess(cmd, accum, fail_msg = None):
    p = subprocess.Popen(cmd, cwd = THIS_DIR, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    (o, e) = p.communicate()
    c_string = str(cmd)
    update_accum(accum, cmd, o, e)
    if p.returncode != 0:
        msg = fail_msg or ("Executing " + c_string + " failed!")
        raise TestFailedError(msg, accum)

def run_claims(file_name):
    out_accum = ["", ""]
    run_subprocess(["pdflatex", file_name], out_accum, "Initial compilation failed")
    run_subprocess(["python", ROOT_DIR + "/verify-claims.py", file_name[:-3] + "clm"], out_accum, "Claim verification error")
    run_subprocess(["pdflatex", file_name], out_accum, "Second compilation failed")

    cmd = ["pdftotext", '-enc', 'ASCII7', file_name[:-3] + "pdf", "-"]
    p = subprocess.Popen(cmd, cwd = THIS_DIR, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    (pdf_text, e) = p.communicate()
    update_accum(out_accum, cmd, pdf_text, e)
    if p.returncode != 0:
        raise TestFailedError("Pdf to text conversion failed", out_accum)
    return (pdf_text, out_accum)

def expect_fail(file_name):
    (text, proc_accum) = run_claims("fail.tex")
    if re.match('\[Claim "[^"]+"\]:[^[]+\[is FALSE\]', text) is None:
        raise TestFailedError(file_name + " expected to fail claim, did not", proc_accum)
    print file_name + ": PASSED"

def expect_pass(file_name):
    (text, proc_accum) = run_claims(file_name)
    if "[Claim" in text:
        raise TestFailedError(file_name + " was expected to pass, did not", proc_accum)
    print file_name + ": PASSED"

def expect_unverified(file_name):
    (text, proc_accum) = run_claims(file_name)
    if re.match('\[Claim "[^"]+"\]:[^]]+\[is unverified\]', text) is None:
        raise TestFailedError(file_name + " was expected to be unverified, was not", proc_accum)
    print file_name + ": PASSED"

shutil.copy(ROOT_DIR + "/claims.sty", THIS_DIR)

def cleanup():
    subprocess.call("rm *.pdf *.aux *.vld *.clm *.log", cwd = THIS_DIR, shell=True)

try:
    expect_fail("fail.tex")
    expect_pass("invert.tex")
    expect_pass("no-quote.tex")
    expect_unverified("unverified.tex")
except TestFailedError as e:
    print "Test FAILED"
    print e.message
    print e.output[0]
    print e.output[1]

cleanup()
