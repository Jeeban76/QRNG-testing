create a requirements file 
this should contain all the library and packages for the streamlit ui
the library used in this project can be easilly found in app_3 .
copy the library name and paste it in requiremnt.tx in the format library=>version
" Install dependencies"
pip install -r requirements.txt


 Launch the app
streamlit run app.py


# database schema

```sql
experiments      -- run metadata (source, bits, config)
test_results     -- per-test p-values and pass/fail
entropy_metrics  -- Shannon & min-entropy per run
derived_keys     -- KDF output (key hex, salt, method)
```

---

## Bit Sources

| Source | Description | Randomness Quality |
|---|---|---|
| OS / Crypto PRNG | `os.urandom()` — hardware entropy pool | ✅ Cryptographic |
| NumPy MT | Mersenne-Twister — fast but weaker | ⚠️ Statistical only |
| Biased Stream | Intentionally biased (P(1) = 0.7) | ❌ Weak / test baseline |
| Qiskit Quantum Sim | Hadamard gate + measurement via AerSimulator | ✅ Quantum |
| Upload QRNG File | External QRNG data (.txt bits or binary) | Depends on source |

---

## NIST SP 800-22 Tests Implemented

1. **Frequency (Monobit)** — Tests overall 0/1 balance
2. **Block Frequency** — Tests balance within M-bit blocks
3. **Runs** — Tests lengths of consecutive identical bits
4. **Longest Run of Ones** — Tests longest run within blocks
5. **Serial** — Tests overlapping m-bit pattern distribution

All tests use α = 0.01 as the significance threshold.
