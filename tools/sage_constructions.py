# Run inside the SageMath docker image (no network, one CPU):
#   docker run --rm --network none --cpus 1 -v <dir>:/w sagemath/sagemath:latest \
#       sage -python /w/sage_constructions.py /w/params.txt /w/sage_constructions.tsv
# params.txt: one "v k lambda mu" per line (all rows of Brouwer's table).
# Output TSV columns: v k l mu existence constructor test args seconds
#   existence   = graphs.strongly_regular_graph(v,k,l,mu,existence=True): True / False / Unknown
#   constructor = name of the function Sage's strongly_regular_db would call (when True)
#   test        = first Sage is_* recogniser accepting the row; 'complement:<test>' when only
#                 the complement is recognised; 'database' for Sage's built-in sporadic list
# The script resumes: rows already in the output file are skipped.
import sys, time, signal
from sage.all import graphs, Integer
from sage.graphs.strongly_regular_db import strongly_regular_graph_lazy
import sage.graphs.strongly_regular_db as _db

TESTS = [n for n in dir(_db) if n.startswith('is_') and n not in ('is_prime_power', 'is_square')]


class TO(Exception):
    pass


def _alarm(signum, frame):
    raise TO()


def which_test(v, k, l, mu):
    for n in TESTS:
        try:
            if getattr(_db, n)(v, k, l, mu):
                return n
        except TO:
            raise
        except Exception:
            pass
    return ''


signal.signal(signal.SIGALRM, _alarm)
src, dst = sys.argv[1], sys.argv[2]
rows = [tuple(int(x) for x in ln.split()) for ln in open(src) if ln.strip()]
done = set()
try:
    for ln in open(dst):
        p = ln.split('\t')
        if p[0].isdigit():
            done.add(tuple(int(x) for x in p[:4]))
except OSError:
    pass
out = open(dst, 'a')
if not done:
    out.write('v\tk\tl\tmu\texistence\tconstructor\ttest\targs\tseconds\n')
for (v, k, l, mu) in rows:
    if (v, k, l, mu) in done:
        continue
    t0 = time.time()
    ex, name, tst, args = 'Error', '', '', ''
    V, K, L, M = Integer(v), Integer(k), Integer(l), Integer(mu)
    signal.alarm(90)
    try:
        e = graphs.strongly_regular_graph(V, K, L, M, existence=True)
        ex = str(e)
        if e is True:
            try:
                lz = strongly_regular_graph_lazy(V, K, L, M)
                f = lz[0]
                name = getattr(f, '__qualname__', None) or getattr(f, '__name__', repr(f))
                name = name.replace('.<locals>', '')
                args = repr(tuple(lz[1:]))[:200].replace('\t', ' ').replace('\n', ' ')
            except TO:
                raise
            except Exception as exc:
                name = 'lazy-error:' + type(exc).__name__
            tst = which_test(V, K, L, M)
            if not tst:
                c = which_test(V, V - K - 1, V - 2 - 2 * K + M, V - 2 * K + L)
                tst = ('complement:' + c) if c else 'database'
    except TO:
        ex = ex if ex != 'Error' else 'Timeout'
        tst = tst or 'timeout'
    except Exception as exc:
        ex = 'Error:' + type(exc).__name__
    finally:
        signal.alarm(0)
    out.write('%d\t%d\t%d\t%d\t%s\t%s\t%s\t%s\t%.1f\n' % (v, k, l, mu, ex, name, tst, args, time.time() - t0))
    out.flush()
out.close()
