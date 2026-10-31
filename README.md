<p align="center"><img src="assets/logo.svg" width="120" alt="GLAW"></p>

# GLAW

**G**lobal-**L**ocal **A**greement-**W**eighted Dual-Feature Learning for Text-Based Person Search

## Method Overview

GLAW tackles **Text-Based Person Search (TBPS)** — retrieving person images from a gallery using natural language descriptions. Our framework combines three novel components built on CLIP ViT-B/16:

| Component | Description |
|-----------|-------------|
| **CMATS** | Cross-Modal Attention-guided Token Selection — selects discriminative visual patches and textual tokens using bidirectional cross-modal attention weights |
| **GLAW Loss** | Agreement-weighted Dual TAL loss — global branch + token-selected local branch, weighted by image-text agreement scores via sigmoid |
| **FDR** | Feature Denoising Regularization — injects Gaussian noise into bypass features and matches noisy/clean cosine similarities via MSE |
| **Centroid Loss** | EMA-updated class centroids — pulls features toward identity centroids weighted by agreement, centroids updated from clean samples |

### Architecture

- **Backbone**: OpenAI CLIP ViT-B/16 (image encoder) + CLIP Transformer (text encoder)
- **Token Selection**: CMATS layers select top-k (30%) visual patches and text tokens using cross-modal attention importance scores
- **Loss**: `GLAW` + `FDR` + `Centroid` (all computed jointly in forward pass)

---

## Performance

| Dataset | t2i R1 | t2i R5 | t2i R10 | t2i mAP | t2i mINP |
|--------|--------|--------|---------|---------|----------|
| CUHK-PEDES | **74.27** | 89.80 | 94.15 | 66.36 | 50.06 |
| ICFG-PEDES | **65.82** | 81.24 | 86.77 | 39.22 | 7.66 |
| RSTPReid | **65.60** | 83.80 | 90.30 | 50.89 | 28.13 |

---

## Requirements

- PyTorch >= 1.10 (CUDA build recommended)
- OpenAI CLIP ViT-B/16 weights (downloaded automatically by `clip` on first use)

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Datasets

Download and place the datasets under `data/` with the following structure:

```
data/
├── CUHK-PEDES/
│   ├── imgs/CUHK03/         # person images
│   ├── imgs/cam_a/          # person images (camera A)
│   ├── reid_raw.json        # train/val/test split annotations
│   └── caption_all.json     # caption annotations (optional)
├── ICFG-PEDES/
│   ├── imgs/                # person images
│   └── ICFG-PEDES.json      # annotations
└── RSTPReid/
    ├── imgs/                # person images
    └── data_captions.json   # annotations
```

---

## Training

### Direct Training

```bash
mkdir -p logs

python train.py \
  --name GLAW_centroid \
  --dataset_name RSTPReid \
  --loss_names glaw \
  --num_epoch 60 \
  --batch_size 64 \
  --lr 5e-6 \
  --temperature 0.02 \
  --tau 0.015 \
  --margin 0.1 \
  --select_ratio 0.3 \
  --cm_alpha 0.5 \
  --eval_period 1 \
  --log_period 50 \
  --num_workers 4 \
  --root_dir data \
  --img_aug \
  --txt_aug \
  --fdr_weight 1.0 \
  --noise_std 0.1 \
  --centroid_weight 0.5 \
  --centroid_momentum 0.99
```

### Resume from Checkpoint

```bash
python train.py \
  ... \
  --resume \
  --resume_ckpt_file logs/RSTPReid/20260804_121136_GLAW_centroid_glaw/best.pth
```

---

## Key Hyperparameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--lr` | 1e-5 | Learning rate |
| `--batch_size` | 128 | Batch size |
| `--num_epoch` | 60 | Training epochs |
| `--temperature` | 0.02 | Logit scaling temperature |
| `--tau` | 0.015 | Temperature for TAL loss softmax |
| `--margin` | 0.1 | Margin for TAL triplet constraint |
| `--select_ratio` | 0.3 | Ratio of top-k tokens selected by CMATS |
| `--cm_alpha` | 0.5 | Cross-modal attention weight in CMATS |
| `--fdr_weight` | 1.0 | Weight for FDR regularization loss |
| `--noise_std` | 0.1 | Std of Gaussian noise in FDR |
| `--centroid_weight` | 0.5 | Weight for centroid loss |
| `--centroid_momentum` | 0.99 | EMA momentum for centroid update |
| `--img_aug` | False | Enable random crop/erase augmentation |
| `--txt_aug` | False | Enable text augmentation |
| `--sampler` | random | Sampler type: [random, identity] |
| `--num_instance` | 4 | Instances per ID (identity sampler only) |
| `--lrscheduler` | cosine | LR schedule: [cosine, multi_step] |

---

## Evaluation

```bash
python test.py --config_file logs/<dataset>/<timestamp>_<name>_<loss_names>/configs.yaml
```

This loads the saved model checkpoint and evaluates on the test set, producing t2i (text-to-image) retrieval metrics.

---

## Training Details

- **Optimizer**: Adam, weight decay 4e-5
- **LR Schedule**: Cosine annealing with 5-epoch linear warmup
- **Training Epochs**: 60
- **Image Size**: 384 x 128

During training, training-time Gaussian noise (`--noise_std=0.1`) is added to both global and token-selected bypass features before loss computation. The model evaluates every epoch on the test set.

---

## Citation

If you find this work useful, please consider citing:

```bibtex
@misc{xu2026glaw,
  title  = {GLAW: Global-Local Agreement-Weighted Dual-Feature Learning for Text-Based Person Search},
  author = {Zhe Xu and Haoning Deng and Zhengye Zhang and Zhijie Yao and Kun Zhang*},
  year   = {2026},
  note   = {Manuscript submitted for publication}
}
```

(* corresponding author) This entry will be updated once the paper is published.

---

## License

Released under the [MIT License](LICENSE).

This project includes code adapted from [OpenAI CLIP](https://github.com/openai/CLIP), which is
distributed under the MIT License.
