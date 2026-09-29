# MAIN_GROWTH_V2 — Canonical 1m Data Location and Recovery

## Important correction

Do NOT assume MNQ/NQ/YM/RTY exist only as Google Drive chunks.

A canonical inventory dated 2026-09-23 recorded that **full NQ and MNQ parquet files survived locally** at:

`C:\Users\User\Documents\ChatGPT\grid_max_portability\data\raw\portability_v1\`

The older folder:

`C:\Users\User\Desktop\massive_data\`

was recorded as no longer existing.

Before downloading anything from Drive, search the PC for valid full canonical files and verify by SHA256.

## Canonical identities

| Symbol | Expected bytes | Expected SHA256 |
|---|---:|---|
| ES | 38,881,868 | 2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116 |
| MNQ | 42,698,119 | 66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2 |
| NQ | 42,585,079 | e6298965fb7ba71efd9114c4f303e393eb9d8e0ae2ddb290aa42daae0c64c663 |
| RTY | 38,456,161 | 7539af4407ca8c5e149c4b9e006ac691323b7a736bfc5fbe2788bfd2a6246999 |
| YM | 39,312,525 | edde4419b90e6545bb8f170bbf009622275ef1b1ad5fbe974952364e3ea0a6d5 |

These hashes are the identity authority. A file with the right name but wrong hash is NOT canonical.

## Local search order

### 1. First check the known surviving location

PowerShell:

```powershell
$known = "$env:USERPROFILE\Documents\ChatGPT\grid_max_portability\data\raw\portability_v1"
Get-ChildItem $known -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '^canonical_1m_(MNQ|NQ|YM|RTY)\.parquet$' } |
  Select-Object FullName, Length
```

Then verify hashes:

```powershell
Get-ChildItem $known -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '^canonical_1m_(MNQ|NQ|YM|RTY)\.parquet$' } |
  ForEach-Object {
    [PSCustomObject]@{
      Path   = $_.FullName
      Bytes  = $_.Length
      SHA256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    }
  }
```

### 2. Search likely project roots

Search these before scanning the entire drive:

- `$env:USERPROFILE\Documents\ChatGPT`
- `$env:USERPROFILE\Desktop\WFB_ULT`
- `$env:USERPROFILE\Desktop`
- current dashboard/research workspace
- any local clone containing `futures_withdrawal_engine/runs/`

PowerShell:

```powershell
$roots = @(
  "$env:USERPROFILE\Documents\ChatGPT",
  "$env:USERPROFILE\Desktop\WFB_ULT",
  "$env:USERPROFILE\Desktop"
)

foreach ($root in $roots) {
  if (Test-Path $root) {
    Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Name -match '^canonical_1m_(MNQ|NQ|YM|RTY)\.parquet$'
      } |
      Select-Object FullName, Length
  }
}
```

Hash every candidate before use.

### 3. Broad fallback search

Only if the targeted searches fail:

```powershell
Get-ChildItem C:\Users\User -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Name -match '^canonical_1m_(MNQ|NQ|YM|RTY)\.parquet$'
  } |
  Select-Object FullName, Length
```

Do not scan system folders or unrelated drives unless necessary.

## Google Drive recovery

### NQ / RTY / YM

TEST43 chunk folder:

`TEST43_CLAUDE_OPTIMIZATION_LAB_ES_3M_2026-09/00_DATA_CHUNKS_FOR_CLAUDE`

Drive Folder ID:

`1Jy5-WEG69Oo9bvGori0GNAQs38sEUoi8`

This package was documented to contain:

- canonical_1m_ES.parquet.part000 ... part005
- canonical_1m_NQ.parquet.part000 ... part005
- canonical_1m_RTY.parquet.part000 ... part005
- canonical_1m_YM.parquet.part000 ... part005
- TEST43_DATA_CHUNKS_MANIFEST.json
- TEST43_DATA_CHUNKS_README.txt

Each part is a raw byte slice, not a parquet file.

Concatenate all six parts lexically, then verify exact size + SHA256 above.

### MNQ

MNQ has a separate 1 MB chunk package.

README Drive file:

`TEST43_MNQ_DATA_CHUNKS_README_1MB.txt`

README file ID:

`1ETyFef14XWzmR2mapf74-W5oRb7aRc-k`

Chunk folder parent ID recorded by Drive:

`1RWREcxqinQ-cTSf_UeckQN2-CMKTdlTb`

Original source Drive file ID:

`1UdBYP0GqDvRaIREk5g_duuIvtwRn7CMz`

Expected MNQ source:

- file: `canonical_1m_MNQ.parquet`
- bytes: 42,698,119
- SHA256: `66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2`
- chunk size: <= 1,000,000 bytes
- chunk count: 43

Concatenate parts lexically and verify BEFORE parsing.

## Original Drive canonical folder

A 2026-09-23 canonical inventory recorded the original Drive source folder as:

`1Qpbw_v6qARoCgLjgEvnRfgwYxV2fs15r`

It contained canonical index futures files including ES/NQ/RTY/YM and also MNQ outside the TEST32 universe.

Prefer an already-valid local full file over re-downloading chunks.

## Reconstruction

Never parse a part individually.

Python:

```python
from pathlib import Path
import hashlib

def rebuild(folder: Path, symbol: str, expected_sha: str, expected_size: int):
    parts = sorted(folder.glob(f"canonical_1m_{symbol}.parquet.part*"))
    if not parts:
        raise RuntimeError(f"No chunks found for {symbol}")

    out = folder / f"canonical_1m_{symbol}.parquet"
    with out.open("wb") as w:
        for p in parts:
            w.write(p.read_bytes())

    size = out.stat().st_size
    sha = hashlib.sha256(out.read_bytes()).hexdigest()

    if size != expected_size:
        raise RuntimeError(f"{symbol}: size mismatch {size} != {expected_size}")
    if sha != expected_sha:
        raise RuntimeError(f"{symbol}: SHA mismatch {sha} != {expected_sha}")

    print(symbol, "PASS", size, sha)
    return out
```

For large files, a streaming hash implementation is preferred instead of `read_bytes()`, but the identity values above remain the same.

## Dashboard requirement

The dashboard integration should resolve data paths through one local data registry/config.

Do NOT hard-code multiple copies in strategy code.

Recommended normalized paths:

```text
<data_root>/canonical_1m_ES.parquet
<data_root>/canonical_1m_MNQ.parquet
<data_root>/canonical_1m_NQ.parquet
<data_root>/canonical_1m_YM.parquet
<data_root>/canonical_1m_RTY.parquet
```

On startup:
1. confirm every required file exists,
2. confirm size,
3. confirm SHA256 when installing/importing the dataset,
4. fail closed if required data is absent or mismatched.

For routine dashboard runs, cache the verified identity so a 40 MB SHA scan does not have to block every UI refresh.
