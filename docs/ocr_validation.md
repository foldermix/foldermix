# OCR Validation Set

Foldermix supports generating and committing a small OCR validation corpus for regression testing the standalone image OCR path. When present, the committed files live under `tests/data/ocr_validation`, but the source dataset is **not** committed to this repository.

Source dataset:

- Kaggle: [Scanned Images Dataset for OCR and VLM finetuning](https://www.kaggle.com/datasets/suvroo/scanned-images-dataset-for-ocr-and-vlm-finetuning)
- Category layout used by the builder: `ADVE`, `Email`, `Form`, `Letter`, `Memo`, `News`, `Note`, `Report`, `Resume`, `Scientific`

Use the dataset in a way that respects its license and any document-sensitivity / PII considerations before committing derived samples.

## Build Or Refresh The Validation Set

1. Download and unpack the Kaggle dataset locally. Do not automate Kaggle auth in repo scripts or CI.
2. Install OCR dependencies in your checkout:

```bash
pip install -e ".[ocr]"
# or
pip install -e ".[all]"
```

3. Generate the committable sample set:

```bash
python scripts/build_ocr_validation_set.py \
  --dataset-root /path/to/scanned-images-dataset-for-ocr-and-vlm-finetuning \
  --out-dir tests/data/ocr_validation \
  --per-category 5 \
  --seed 1337
```

4. Review and commit the generated files:

- `tests/data/ocr_validation/manifest.json`
- `tests/data/ocr_validation/images/...`
- `tests/data/ocr_validation/expected_text/...`

The builder redacts SSN-like values in generated OCR goldens before writing them to disk. You should still review the sampled files for sensitive content before committing them.

To replace an existing validation set or refresh goldens after a deliberate OCR improvement, rerun with `--force`:

```bash
python scripts/build_ocr_validation_set.py \
  --dataset-root /path/to/scanned-images-dataset-for-ocr-and-vlm-finetuning \
  --out-dir tests/data/ocr_validation \
  --per-category 5 \
  --seed 1337 \
  --force
```

## CI Behavior

- If `tests/data/ocr_validation/manifest.json` is absent, the OCR integration test skips with a clear message so PR CI stays green before the dataset commit is added.
- Once the validation files are committed, CI runs Foldermix OCR on every sampled image and checks for non-empty output plus minimum similarity to the committed goldens.
